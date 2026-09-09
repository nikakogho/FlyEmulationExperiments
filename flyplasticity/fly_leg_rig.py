"""Actual FlyGym foreleg geometry; engineering actuation, no neural dynamics."""
from pathlib import Path
from copy import deepcopy
import xml.etree.ElementTree as ET
import hashlib
import flygym,mujoco,numpy as np
from flyplasticity.joint_rig import JointRig
from flyplasticity.welfare import Guard,Limits

SOURCE=Path(flygym.__file__).parent/'data/mjcf/neuromechfly_seqik_kinorder_ypr.xml'


class FlyLegRig(JointRig):
    def __init__(self, *, neural_model=None):
        if neural_model is not None:raise ValueError('Neural attachment is disabled')
        original=ET.parse(SOURCE).getroot()
        root=ET.Element('mujoco',model='isolated_flygym_foreleg')
        for tag in ['compiler','default','asset']:root.append(deepcopy(original.find(tag)))
        for mesh in root.findall('.//mesh'):
            if 'file' in mesh.attrib:mesh.set('file',str((SOURCE.parent/mesh.get('file')).resolve()))
        ET.SubElement(root,'option',timestep='.001',gravity='0 0 0',integrator='implicitfast')
        visual=ET.SubElement(root,'visual');ET.SubElement(visual,'global',offwidth='800',offheight='608')
        world=ET.SubElement(root,'worldbody')
        leg=deepcopy(original.find(".//body[@name='LFCoxa']"));leg.set('pos','0 0 0');world.append(leg)
        for parent in leg.iter():
            for child in list(parent):
                if child.tag=='joint' and child.get('name')!='joint_LFTibia':parent.remove(child)
        # Keep source mesh, mass, pose, joint axis and damping. Other joints are
        # immobilized at source reference coordinates. No ground or gravity.
        joint=leg.find(".//joint[@name='joint_LFTibia']")
        joint.set('range','.2 1.6');joint.set('limited','true')
        for geom in leg.iter('geom'):geom.set('rgba','0.2 0.7 0.6 1')
        ET.SubElement(world,'light',pos='0 -3 4')
        acts=ET.SubElement(root,'actuator')
        for name,gear in [('flexion','0.006'),('extension','-0.006')]:
            ET.SubElement(acts,'general',name=name,joint='joint_LFTibia',gear=gear,
                          dyntype='filterexact',dynprm='.02',ctrlrange='0 1',forcerange='0 1')
        self.xml=ET.tostring(root,encoding='unicode')
        self.model=mujoco.MjModel.from_xml_string(self.xml);self.data=mujoco.MjData(self.model)
        self.data.qpos[0]=.8
        mujoco.mj_forward(self.model,self.data)
        self.guard=Guard(Limits(4.,.001001,1.01,.05));self.rows=[];self.steps=0

    def camera(self):
        cam=mujoco.MjvCamera();cam.lookat[:]=(self.data.body('LFCoxa').xpos+self.data.body('LFTarsus5').xpos)/2
        cam.distance=4.5;cam.azimuth=135;cam.elevation=-25
        return cam

    def observe(self):
        result=super().observe()
        a=self.data.body('LFFemur').xpos-self.data.body('LFTibia').xpos
        b=self.data.body('LFTarsus1').xpos-self.data.body('LFTibia').xpos
        result['anatomical_angle_deg']=float(np.degrees(np.arccos(np.clip(a@b/np.linalg.norm(a)/np.linalg.norm(b),-1,1))))
        # The parent fixture labels SI torque; this source uses native units.
        result['torque_source_units']=result.pop('torque_nm')
        return result

    def step(self,command,*,fault=False):
        # Reuse the tested guard runner's schema while recording native units.
        # Avoid calling the parent observe override-dependent implementation.
        command=np.asarray(command,dtype=float)
        if command.shape!=(2,) or not np.isfinite(command).all() or (command<0).any() or (command>1).any():
            self.guard._stop('invalid_actuator_command',float(self.data.time));raise ValueError('Bad command')
        from flyplasticity.welfare import Sample
        finite=bool(np.isfinite(np.r_[self.data.qpos,self.data.qvel,self.data.act,self.data.qfrc_actuator]).all())
        sample=Sample(float(self.data.time),float(max(self.data.act)),finite and not fault,True,
                      bool((self.data.qpos[0]<.21 or self.data.qpos[0]>1.59) and max(command)>.1 and abs(self.data.qvel[0])<.01),False)
        def advance():
            self.data.ctrl[:]=command;mujoco.mj_step(self.model,self.data);self.steps+=1
        self.guard.advance(sample,advance)
        row=self.observe();row.update(command=command.tolist(),guard_status=self.guard.events[-1]['status']);self.rows.append(row)
        return row

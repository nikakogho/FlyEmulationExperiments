"""Render odor markers as sites, which cannot acquire contact pairs."""


def noncolliding_odor_markers(arena):
    count=0
    for geom in list(arena.root_element.find_all('geom')):
        if 'odor_source_marker' not in str(getattr(geom.parent,'name','')):continue
        geom.parent.add('site',name=f'odor_visual_{count}',type=geom.type,size=geom.size,rgba=geom.rgba)
        geom.remove();count+=1
    if count==0:raise ValueError('No odor markers found to convert')
    return count

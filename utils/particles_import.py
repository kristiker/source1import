import shared.datamodel as dmx
if __name__ is None:
    import utils.shared.datamodel as dmx

from pathlib import Path

class resource(str): pass  # kv3 resource

#TODO: are arrays different from vectors? vec seems to have no newlines and no comma at end

pcf_to_vpcf = {
    # name/functionName -> class

    'renderers': ( 'm_Renderers', {
            'render_animated_sprites':  'C_OP_RenderSprites',
                'animation rate':           'm_flAnimationRate',
    }),
    
    'operators': ('m_Operators', {
        'Lifespan Decay': 'C_OP_Decay',
        'Radius Scale': 'C_OP_InterpolateRadius',
            'm_flEndScale': 'radius_start_scale',
            'm_flStartScale': 'radius_end_scale',
        'Alpha Fade In Random': 'C_OP_FadeIn',
            'proportional 0/1': 'm_bProportional',
            'fade out time min': 'm_flFadeOutTimeMin',
            'fade out time max': 'm_flFadeOutTimeMax',
            'ease in and out': 'm_bEaseInAndOut',
        'Alpha Fade Out Random': 'C_OP_FadeOut',
            'proportional 0/1': 'm_bProportional',
            'fade out time min': 'm_flFadeOutTimeMin',
            'fade out time max': 'm_flFadeOutTimeMax',
            'ease in and out': 'm_bEaseInAndOut',
        'Movement Basic': 'C_OP_BasicMovement',
            'gravity': 'm_Gravity',
    }),

    'initializers': ('m_Initializers', {
        'Position Within Sphere Random': 'C_INIT_CreateWithinSphere',
            'speed_max': 'm_fSpeedMax',
            'speed_min': 'm_fSpeedMin',
            'distance_max': 'm_fRadiusMax',
        'Lifetime Random': 'C_INIT_RandomLifeTime',
            "lifetime_min": 'm_fLifetimeMin',
            "lifetime_max": 'm_fLifetimeMax',
    
        'Color Random': 'C_INIT_RandomColor',
            'tint clamp max': 'm_TintMax',
            'tint clamp min': 'm_TintMin',
            'color1': 'm_ColorMin',
            'color2': 'm_ColorMax',
            'tint_perc': 'm_flTintPerc',
            'tint blend mode': 'm_nTintBlendMode',

        'Rotation Random': 'C_INIT_RandomRotation',

        'Alpha Random': 'C_INIT_RandomAlpha',
            "alpha_max": 'm_nAlphaMin',
            "alpha_min": 'm_nAlphaMax',

        'Position Modify Offset Random': 'C_INIT_PositionOffset',
            'offset max': 'm_OffsetMin',
            'offset min': 'm_OffsetMax',
    }),

    # this seems more advanced
    # emission_start_time (float) "14"->>
    # m_flStartTime = 
	# {
	# 	m_nType = "PF_TYPE_LITERAL"
	# 	m_flLiteralValue = 14.0
	# }
    
    'emitters': ('m_Emitters', {
        'emit_instantaneously': ('C_OP_InstantaneousEmitter', {
            'num_to_emit': 'm_nParticlesToEmit',
            'emission_start_time': 'm_flStartTime',
        }),
    }),
    'children':     'm_Children',
    'forces':       '',
    'constrains':   '',

    # bare replacement
    'preventNameBasedLookup':           '',
    'max_particles':                    'm_nMaxParticles',
    'initial_particles':                '',
    'cull_replacement_definition':      '',
    'fallback replacement definition':  'm_hFallback', # not a string on pcf, its value is an id
    'fallback max count':               'm_nFallbackMaxCount',
    'radius':                           'm_flConstantRadius',
    'color':                            '',
    'maximum draw distance':            'm_flMaxDrawDistance',
    'time to sleep when not drawn':     '',
    'Sort particles':                   'm_bShouldSort',
    'bounding_box_min':                 'm_BoundingBoxMin',
    'bounding_box_max':                 'm_BoundingBoxMax',

    'material':                         ('m_Renderers', 'm_hTexture'),
}

explosions_fx = Path(r'D:\Users\kristi\Documents\GitHub\source1import\utils\shared\particles\explosions_fx.pcf')
lightning = Path(r'D:\Users\kristi\Documents\GitHub\source1import\utils\shared\particles\lighting.pcf')

x = dmx.load(explosions_fx)

def is_valid_pcf(x: dmx.DataModel):
    return ('particleSystemDefinitions' in x.elements[0].keys() and
            x.elements[1].type == 'DmeParticleSystemDefinition'      
        )

def tests():
    print(x.elements[0].keys())
    print(x.elements[1].type)

def pcfkv_convert(key, value):

    if not (vpcf_translation:= pcf_to_vpcf.get(key)):
        print('cant translate', key, value)
        return

    outKey, outVal = key, value

    if isinstance(vpcf_translation, str):  # simple translation
        if value == []: return
        return vpcf_translation, value
    elif isinstance(vpcf_translation, tuple):
        if isinstance(vpcf_translation[1], str):  # insert to another dict
            return
        elif isinstance(vpcf_translation[1], dict):
            if not isinstance(value, list):
                print(key, "is not a ot a list?", value)
                return
            outKey = vpcf_translation[0]
            outVal = []
            subkeytrns = vpcf_translation[1]

            for dm in value:
                if not (className := subkeytrns.get(dm.name)):
                    print(f'cant translate "{outKey}" operator "{dm.name}"')
                    continue
                if isinstance(className, tuple):
                    className, subkeytrns = className
                subKV = { '_class': className }

                for key, value in dm.items():
                    if key == 'functionName':
                        continue
                        
                    if isinstance(vpcf_translation[1].get(dm.name), tuple):
                        value = {'m_nType': "PF_TYPE_LITERAL",'m_flLiteralValue': value}

                    if subkey:=subkeytrns.get(key):
                        subKV[subkey] = value
                    else:
                        print(f'cant translate "{dm.name}":"{key}"')
                        
                outVal.append(subKV)

    return outKey, outVal

def dict_to_kv3_text(d):
    kv3 = '<!-- kv3 encoding:text:version{e21c7f3c-8a33-41c5-9977-a76d3a32aa0d} format:vpcf26:version{26288658-411e-4f14-b698-2e1e5d00dec6} -->\n'

    def obj_serialize(obj, indent = 1):
        if obj is None:
            return 'null'
        elif isinstance(obj, bool):
            if obj: return 'true'
            return 'false'
        elif isinstance(obj, str):
            return '"' + obj + '"'
        elif isinstance(obj, resource):
            return f'resource:"{obj}"'
        elif isinstance(obj, list):
            print("is list", obj)
            s = '['
            for item in obj:
                print(item)
                #print(f'{obj_serialize(item, indent=indent+1)}, ', end='') # ?>??? why inf recursion
            return '[]'#s + ']'
            return f'[{", ".join((obj_serialize(item, indent=indent+1) for item in obj))},]'
        elif isinstance(obj, dict):
            s = '{\n'
            for key, value in d.items():
                s += ('\t' * indent) + f"{key} = {obj_serialize(value, indent=indent+1)}\n"
            return s + '}\n'
        else:
            return obj

    kv3 += obj_serialize(d)

    return kv3


if is_valid_pcf(x):
    print('valid')
    for datamodel in x.find_elements(elemtype='DmeParticleSystemDefinition'):
        print(datamodel.type, datamodel.name)
        
        vpcf = {}
        for key, value in datamodel.items():
            if converted_kv:= pcfkv_convert(key, value):
                vpcf[converted_kv[0]] = converted_kv[1]
        
        #pprint.pprint(vpcf)
        break

        #for element in datamodel:
        #    print(f'  {element}')

else:
    print("Invalid!!")
    tests()

import shared.datamodel as dmx
if __name__ is None:
    import utils.shared.datamodel as dmx

from pathlib import Path
particles = Path('particles')
# https://developer.valvesoftware.com/wiki/Particle_System_Overview
# https://developer.valvesoftware.com/wiki/Animated_Particles
# https://developer.valvesoftware.com/wiki/Source_2_Particle_System_Properties

# particles_manifest.txt
# "!" before path means precache all on map spawn
# normal paths get 

BEHAVIOR_VERSION = 9

class dynamicparam(str): pass
class maxof(dynamicparam): pass # for Random Uniform
class minof(dynamicparam): pass # for Random Uniform

class Ref(str):
    "Resource reference"

class ObjectP:
    def __init__(self, object_name: str, param: str=''):
        self.mother = object_name
        self.name = param
    def __str__(self):
        return self.name

class watch:
    def __init__(self, t):
        self.key = t
    def __call__(self,oldval):
        print(self.key, oldval)
        input()
        return self.key, oldval

class remap:
    def __init__(self, t, map):
        self.key = t
        self.map = map
    def __call__(self, oldval):
        return self.key, self.map.get(oldval)

class BoolToSetKV:
    def __init__(self, k, v):
        self.k, self.v = k, v
    def __call__(self, oldval):
        if oldval: return self.k, self.v

class Discontinued:
    "This parameter worked on particle systems with behaviour versions lower than `self.at"
    def __init__(self, t: str='', at: int=-1):
        self.t = t
        self.at = at
    def __bool__(self): return False # FIXME

class Multiple:
    def __init__(self, *args, **kwargs):
        self.bare_replacements = args
        self.kw_replacements = kwargs

class SingleColour:
    default = [255, 255, 255, 255]
    def __init__(self, t: str, place:int) -> None:
        self.t = t
        self.place = place
    def __call__(self, oldval, existing = default):
        rv = existing
        rv[self.place] = oldval
        return self.t, rv

vpcf_PreOPs = set()
def PreOP(cls: str):
    vpcf_PreOPs.add(cls)
    return cls

#TODO: are arrays different from vectors? vec seems to have no newlines and no comma at end

# are pcf keys case insensitive?

# incomplete - contains most common ones
pcf_to_vpcf = {
    # name/functionName -> class
    'renderers': ( 'm_Renderers', {
        'render_animated_sprites':  'C_OP_RenderSprites',
            'animation rate': 'm_flAnimationRate',
            'second sequence animation rate': 'm_flAnimationRate2',
            'cull system when CP normal faces away from camera': Discontinued(),
            'cull system starting at this recursion depth': Discontinued(),
            'use animation rate as FPS': 'm_bAnimateInFPS',
            'animation_fit_lifetime': BoolToSetKV('m_nAnimationType', 'ANIMATION_TYPE_FIT_LIFETIME'),
            'orientation control point': 'm_nOrientationControlPoint',
            'orientation_type': 'm_nOrientationType',
            'length fade in time': Discontinued(),
            'min length': 'm_flMinSize',
            'max length': 'm_flMaxSize',
            'constrain radius to length': Discontinued(),
            'ignore delta time': Discontinued(),
            'sheet': Discontinued(), # probably some obscure m_hTexture ?

        'render_rope': 'C_OP_RenderRopes',
            'texel_size': '',#radius scale?#Multiple('m_flFinalTextureScaleU', 'm_flFinalTextureScaleV'), # unsure
            'texture_scroll_rate': dynamicparam('m_flTextureVScrollRate'),
            'subdivision_count': 'm_flTessScale',
            'scale offset by CP distance': 'm_flScaleVOffsetByControlPointDistance',
            'scale scroll by CP distance': 'm_flScaleVScrollByControlPointDistance',
        'render_screen_velocity_rotate': NotImplemented,
            'forward_angle': '',
        'render_sprite_trail': 'C_OP_RenderTrails',
            'tail color and alpha scale factor': Multiple(
                m_vecTailColorScale = lambda v: v[:3],
                m_flTailAlphaScale = lambda v: v[3:]
            ),
            'Visibility Camera Depth Bias': 'm_flDepthBias', # weird name source engine but ok
        'render_blobs': 'C_OP_RenderBlobs',
            'cube_width': 'm_cubeWidth',
            'cutoff_radius': 'm_cutoffRadius',
            'render_radius': 'm_renderRadius',
            #'scale CP (cube width/cutoff/render = x/y/z)':'m_nScaleCP'
        'Render models': 'C_OP_RenderModels',
            # m_ModelList =
            # [
            # 	 {
            # 	 	m_model = resource:"asd"
            # 	 },
            # ]
            'sequence 0 model': lambda v: ('m_ModelList',
                [{'m_model': resource(Path('models/' + v).with_suffix('.vmdl'))}]
            ),
            'orient model z to normal': 'm_bOrientZ',
            'activity override': 'm_ActivityName',
            'animation rate scale field': 'm_nAnimationScaleField',
        'render_project': 'C_OP_RenderProjected',
    }),

    'operators': ('m_Operators', {
        'Lifespan Decay': 'C_OP_Decay',
        'lifespan_decay': 'C_OP_Decay',
            # m_bRopeDecay
        'Radius Scale': 'C_OP_InterpolateRadius',
            'radius_start_scale': 'm_flStartScale',
            'radius_end_scale': 'm_flEndScale',
            'start_time': 'm_flStartTime',
            'scale_bias': 'm_flBias',
            'end_time': 'm_flEndTime',
            'ease_in_and_out': 'm_bEaseInAndOut',

        'Alpha Fade In Random': 'C_OP_FadeIn',
        'alpha_fade_in_random': 'C_OP_FadeIn',
            'proportional 0/1': 'm_bProportional',
            'fade in time min': 'm_flFadeInTimeMin',
            'fade in time max': 'm_flFadeInTimeMax',
            'fade in time exponent': 'm_flFadeInTimeExp',
            'fade in curve exponent': 'm_flFadeInTimeExp', # i guess?

        'Alpha Fade Out Random': 'C_OP_FadeOut',
        'alpha_fade_out_random': 'C_OP_FadeOut',
            'proportional 0/1': 'm_bProportional',
            'fade out time min': 'm_flFadeOutTimeMin',
            'fade out time max': 'm_flFadeOutTimeMax',
            'ease in and out': 'm_bEaseInAndOut',
            'fade bias': 'm_flFadeBias',
            'fade out time exponent': 'm_flFadeOutTimeExp',

        'Movement Basic': 'C_OP_BasicMovement',
            'gravity': 'm_Gravity',
            'drag': 'm_fDrag',
            'max constraint passes': 'm_nMaxConstraintPasses',

        'Movement Dampen Relative to Control Point': 'C_OP_DampenToCP',
        'Dampen Movement Relative to Control Point': 'C_OP_DampenToCP',
            # m_nControlPointNumber
            'dampen scale': 'm_flScale',
            'falloff range': 'm_flRange',

        'Alpha Fade and Decay': 'C_OP_FadeAndKill',
        'fade_and_kill': 'C_OP_FadeAndKill',
            'start_fade_in_time': 'm_flStartFadeInTime',
            'end_fade_in_time': 'm_flEndFadeInTime',
            'start_alpha': 'm_flStartAlpha',
            'end_alpha': 'm_flEndAlpha',
            'start_fade_out_time': 'm_flStartFadeOutTime',
            'end_fade_out_time': 'm_flEndFadeOutTime',

        'Rotation Basic': 'C_OP_SpinUpdate',
        'spin': 'C_OP_SpinUpdate',
            'spin_rate': '', # what? Can't be SpinUpdate then FIXME
        'Oscillate Scalar': 'C_OP_OscillateScalar',
        'oscillate_scalar': 'C_OP_OscillateScalar',
            'end time max': 'm_flEndTime_max',
            'end time min': 'm_flEndTime_min',
            'oscillation start phase': 'm_flOscAdd',
            'start/end proportional': 'm_bProportionalOp',
            'absolute oscillation': '',
        'Oscillate Vector': 'C_OP_OscillateVector',
        'oscillate_vector': 'C_OP_OscillateVector',
            'oscillation frequency max': 'm_FrequencyMax',
            'oscillation frequency min': 'm_FrequencyMin',
            'oscillation rate max': 'm_RateMax',
            'oscillation rate min': 'm_RateMin',
            'oscillation field': 'm_nField',
            'oscillation multiplier': 'm_flOscMult',
            'start time max': 'm_flStartTime_max',
            'start time min': 'm_flStartTime_min',
            'end time exponent': Discontinued(),
            'start time exponent': Discontinued(),
            'oscillation frequency exponent': Discontinued(),
            'oscillation rate exponent': Discontinued(),
            # m_bOffset

        'Movement Lock to Control Point': 'C_OP_PositionLock',
        'postion_lock_to_controlpoint': 'C_OP_PositionLock',
            # m_flJumpThreshold, m_flPrevPosScale
            'lock rotation': 'm_bLockRot',
            'start_fadeout_min': 'm_flStartTime_min',
            'start_fadeout_max': 'm_flStartTime_max',
            'end_fadeout_min': 'm_flEndTime_min',
            'end_fadeout_max': 'm_flEndTime_max',
            'control_point_number': 'm_nControlPointNumber',
            'end_fadeout_exponent': 'm_flEndTime_exp',
            'start_fadeout_exponent': 'm_flStartTime_exp',
            'distance fade range': 'm_flRange',
        'Cull when crossing sphere': 'C_OP_DistanceCull',
            'Cull Distance': 'm_flDistance',
            'Cull inside instead of outside': 'm_bCullInside',
            'Control Point': 'm_nControlPoint',
            # m_flPlaneOffset is from `...crossing plane`
            'Cull plane offset': 'm_flPlaneOffset', # this is a float.. what m_vecPointOffset
        'Remap Distance to Control Point to Scalar': 'C_OP_DistanceToCP',
            'output maximum': 'm_flOutputMax',
            'output minimum': 'm_flOutputMin',
            'output field': 'm_nFieldOutput',
            'distance maximum': 'm_flInputMax',
            'distance minimum': 'm_flInputMin',
            'output is scalar of initial random range': BoolToSetKV('m_nSetMethod', "PARTICLE_SET_SCALE_INITIAL_VALUE"),
            'output is scalar of current value': BoolToSetKV('m_nSetMethod', "PARTICLE_SET_SCALE_CURRENT_VALUE"),
            'only active within specified distance': 'm_bActiveRange',
            'control point': 'm_nControlPoint',
        'Color Fade': 'C_OP_ColorInterpolate',
            'color_fade': 'm_ColorFade',
            'fade_start_time': 'm_flFadeStartTime',
            'fade_end_time': 'm_flFadeEndTime',
        'Rotation Spin Roll': 'C_OP_Spin',
            'spin_rate_degrees': 'm_nSpinRateDegrees',
            'spin_stop_time': 'm_fSpinRateStopTime',
            'spin_rate_min': 'm_nSpinRateMinDegrees',
        'Alpha Fade In Simple': 'C_OP_FadeInSimple',
            'proportional fade in time': 'm_flFadeInTime',
        'Cull when crossing plane': 'C_OP_PlaneCull',
            'Control Point for point on plane': 'm_nPlaneControlPoint',
            'Plane Normal': 'm_vecPlaneDirection',
        'Set child control points from particle positions': 'C_OP_SetChildControlPoints',
            '# of control points to set': 'm_nNumControlPoints',
            'First control point to set': 'm_nFirstControlPoint',
            'first particle to copy': dynamicparam('m_nFirstSourcePoint'),
            'Group ID to affect': 'm_nChildGroupID',
            'Set cp orientation for particles': 'm_bSetOrientation',
            'Set cp density for particles': Discontinued(),
            'Set cp velocity for particles': Discontinued(),
            'Set cp radius for particles': Discontinued(),
        'Alpha Fade Out Simple': 'C_OP_FadeOutSimple',
            'proportional fade out time': 'm_flFadeOutTime',
        'Ramp Scalar Linear Random': 'C_OP_RampScalarLinear',
            'ramp rate min': 'm_RateMin',
            'ramp rate max': 'm_RateMax',
            'ramp field': 'm_nField',
        'Remap Speed to Scalar': 'C_OP_RemapSpeed',
            'input maximum': 'm_flInputMax',
            'input minimum': 'm_flInputMin',
        'Lifespan Minimum Velocity Decay': 'C_OP_VelocityDecay',
            'minimum velocity': 'm_flMinVelocity',
        'Rotation Orient Relative to CP': 'C_OP_Orient2DRelToCP',
            'Rotation Offset': 'm_flRotOffset',
            'Spin Strength': 'm_flSpinStrength',
            # rotation field m_nFieldOutput
        'Movement Lock to Bone': 'C_OP_LockToBone',
        'lock to bone': 'C_OP_LockToBone',
            'lifetime fade start': 'm_flLifeTimeFadeStart',
            'lifetime fade end': 'm_flLifeTimeFadeEnd',
        'Cull Random': 'C_OP_Cull',
        'Random Cull': 'C_OP_Cull',
            'Cull Percentage': 'm_flCullPerc',
            'Cull End Time': 'm_flCullEnd',
            'Cull Start Time': 'm_flCullStart',
            'Cull Time Exponent': 'm_flCullExp',
        'Movement Place On Ground': 'C_OP_MovementPlaceOnGround',
            'include water': 'm_bIncludeWater',
            'max trace length': 'm_flMaxTraceLength',
            'collision group': 'm_CollisionGroupName',
            'offset': 'm_flOffset',
            'kill on no collision': 'm_bKill',
            'interpolation rate': 'm_flLerpRate',
        'Remap Scalar': 'C_OP_RemapScalar',
            'input field': 'm_nFieldInput',
        'Lifespan Maintain Count Decay': 'C_OP_DecayMaintainCount',
        'Remap Control Point to Vector': 'C_OP_RemapCPtoVector',
        'Color Light from Control Point': 'C_OP_ControlpointLight',
        'Color Light From Control Point': 'C_OP_ControlpointLight',
            'Compute Normals From Control Points': 'm_bUseNormal',
            'Half-Lambert Normals': 'm_bUseHLambert',
            'Clamp Minimum Light Value to Initial Color': 'm_bClampLowerRange',
            'Clamp Maximum Light Value to Initial Color': 'm_bClampUpperRange',
            'Initial Color Bias': 'm_flScale',
            'Light 1 Control Point': 'm_nControlPoint1',
            'Light 2 Control Point': 'm_nControlPoint2',
            'Light 3 Control Point': 'm_nControlPoint3',
            'Light 4 Control Point': 'm_nControlPoint4',
            'Light 1 Control Point Offset': 'm_vecCPOffset1',
            'Light 2 Control Point Offset': 'm_vecCPOffset2',
            'Light 3 Control Point Offset': 'm_vecCPOffset3',
            'Light 4 Control Point Offset': 'm_vecCPOffset4',
            'Light 1 50% Distance': 'm_LightFiftyDist1',
            'Light 1 0% Distance': 'm_LightZeroDist1',
            'Light 2 50% Distance': 'm_LightFiftyDist2',
            'Light 2 0% Distance': 'm_LightZeroDist2',
            'Light 3 50% Distance': 'm_LightFiftyDist3',
            'Light 3 0% Distance': 'm_LightZeroDist3',
            'Light 4 50% Distance': 'm_LightFiftyDist4',
            'Light 4 0% Distance': 'm_LightZeroDist4',
            'Light 1 Color': 'm_LightColor1',
            'Light 2 Color': 'm_LightColor2',
            'Light 3 Color': 'm_LightColor3',
            'Light 4 Color': 'm_LightColor4',
            'Light 1 Type 0=Point 1=Spot': 'm_bLightType1',
            'Light 2 Type 0=Point 1=Spot': 'm_bLightType2',
            'Light 3 Type 0=Point 1=Spot': 'm_bLightType3',
            'Light 4 Type 0=Point 1=Spot': 'm_bLightType4',
            'Light 1 Dynamic Light': 'm_bLightDynamic1',
            'Light 2 Dynamic Light': 'm_bLightDynamic2',
            'Light 3 Dynamic Light': 'm_bLightDynamic3',
            'Light 4 Dynamic Light': 'm_bLightDynamic4',
            'Light 1 Direction': Discontinued(),
            'Light 2 Direction': Discontinued(),
            'Light 3 Direction': Discontinued(),
            'Light 4 Direction': Discontinued(),
            'Light 1 Spot Inner Cone': Discontinued(),
            'Light 1 Spot Outer Cone': Discontinued(),
            'Light 2 Spot Inner Cone': Discontinued(),
            'Light 2 Spot Outer Cone': Discontinued(),
            'Light 3 Spot Inner Cone': Discontinued(),
            'Light 3 Spot Outer Cone': Discontinued(),
            'Light 4 Spot Inner Cone': Discontinued(),
            'Light 4 Spot Outer Cone': Discontinued(),
        'Movement Max Velocity': 'C_OP_MaxVelocity',
            'Maximum Velocity': 'm_flMaxVelocity',
        'Remap Dot Product to Scalar': 'C_OP_RemapDotProductToScalar',
        'remap dot product to scalar': 'C_OP_RemapDotProductToScalar',
            'first input control point': 'm_nInputCP1',
            'second input control point': 'm_nInputCP2',
            'input minimum (-1 to 1)': 'm_flInputMin',
            'input maximum (-1 to 1)': 'm_flInputMin',
            'only active within specified input range': 'm_bActiveRange',
            'use particle velocity for first input': 'm_bUseParticleVelocity',
            # m_bUseParticleNormal
			# m_nSetMethod = PARTICLE_SET_REPLACE_VALUE "PARTICLE_SET_SCALE_INITIAL_VALUE" "PARTICLE_SET_ADD_TO_INITIAL_VALUE" PARTICLE_SET_SCALE_CURRENT_VALUE PARTICLE_SET_ADD_TO_CURRENT_VALUE
        'Remap Distance Between Two Control Points to Scalar': 'C_OP_DistanceBetweenCPs',
            'starting control point': 'm_nStartCP',
            'ending control point': 'm_nEndCP',
            'ensure line of sight': 'm_bLOS',
            'LOS collision group': 'm_CollisionGroupName',
            'Maximum Trace Length': 'm_flMaxTraceLength',
            'LOS Failure Scalar': 'm_flLOSScale',
        'Remap Control Point to Scalar': 'C_OP_RemapCPtoScalar',
            'input control point number': 'm_nCPInput',
            'input field 0-2 X/Y/Z': 'm_nField',
            'emitter lifetime start time (seconds)': 'm_flStartTime',
            'emitter lifetime end time (seconds)': 'm_flEndTime',
            # m_flInterpRate interp scale
        'Movement Match Particle Velocities': 'C_OP_VelocityMatchingForce',
            'Speed Matching Strength': 'm_flSpdScale',
            'Direction Matching Strength': 'm_flDirScale',
            'Control Point to Broadcast Speed and Direction To': 'm_nCPBroadcast',
        'Set Control Point Positions': PreOP('C_OP_SetControlPointPositions'),
            'First Control Point Location': 'm_vecCP1Pos',
            'Second Control Point Location': 'm_vecCP2Pos',
            'Third Control Point Location': 'm_vecCP3Pos',
            'Fourth Control Point Location': 'm_vecCP4Pos',
            'First Control Point Number': 'm_nCP1',
            'Second Control Point Number': 'm_nCP2',
            'Third Control Point Number': 'm_nCP3',
            'Fourth Control Point Number': 'm_nCP4',
            'Control Point to offset positions from': 'm_nHeadLocation',
            'First Control Point Parent': Discontinued(),
            'Second Control Point Parent': Discontinued(),
            'Third Control Point Parent': Discontinued(),
            'Fourth Control Point Parent': Discontinued(),
            'Set positions in world space': 'm_bUseWorldLocation',
            # m_bOrient m_bSetOnce
        'Set Control Point to Impact Point': PreOP('C_OP_SetControlPointToImpactPoint'),
            'Trace Update Rate': 'm_flUpdateRate',
            'Trace Direction Override': 'm_vecTraceDir',
            'Control Point to Set': 'm_nCPOut',
            'trace collision group': 'm_CollisionGroupName',
            'Control Point to Trace From': 'm_nCPIn',
            'Offset End Point Amount': 'm_flOffset',
            'Max Trace Length': 'm_flTraceLength',
            # m_bSetToEndpoint
        "Set Control Point To Particles' Center": PreOP('C_OP_SetControlPointToCenter'),
            'Control Point Number to Set': 'm_nCP1',
            'Center Offset': 'm_vecCP1Pos', # duplicate????? why have you done this
            'center offset': 'm_vecCP1Pos',
            'basic_movement': Discontinued(),
        'radius_scale': 'C_OP_InterpolateRadius',
        'alpha_fade': 'C_OP_FadeAndKill', # C_OP_FadeOutSimple
        'rotation_spin': 'C_OP_Spin', # rotation spin roll ?????
        'Rotation Spin Yaw': 'C_OP_SpinYaw',
        'rotation_spin yaw': 'C_OP_SpinYaw',
            'yaw_rate_degrees': 'm_nSpinRateDegrees',
            'yaw_rate_min': 'm_nSpinRateMinDegrees',
            'yaw_stop_time': 'm_fSpinRateStopTime',
        'Remap CP Speed to CP': PreOP('C_OP_RemapSpeedtoCP'),
            'input control point': 'm_nInControlPointNumber',
            'output control point': 'm_nOutControlPointNumber',
            'Output field 0-2 X/Y/Z': 'm_nField', # didnt check
        'Remap Difference of Sequential Particle Vector to Scalar': 'C_OP_DifferencePreviousParticle',
            'difference minimum': 'm_flInputMin',
            'difference maximum': 'm_flInputMax',
            'also set ouput to previous particle': 'm_bSetPreviousParticle',
        'Movement Maintain Position Along Path': 'C_OP_MaintainSequentialPath',
            'particles to map from start to end': 'm_flNumToAssign',
            'cohesion strength': 'm_flCohesionStrength',
            'maximum distance': 'm_fMaxDistance',
            'restart behavior (0 = bounce, 1 = loop )': 'm_bLoop',
            'use existing particle count': 'm_bUseParticleCount',
            'control point movement tolerance': 'm_flTolerance',
            **(_m_PathParams:={'bulge': ObjectP('m_PathParams', 'm_flBulge'), # random bulge? m_flBulge
            'start control point number': ObjectP('m_PathParams', 'm_nStartControlPointNumber'),
            'end control point number': ObjectP('m_PathParams', 'm_nEndControlPointNumber'),
            'bulge control 0=random 1=orientation of start pnt 2=orientation of end point':\
                ObjectP('m_PathParams', 'm_nBulgeControl'),
            'mid point position': ObjectP('m_PathParams', 'm_flMidPoint'),}),
        'Ramp Scalar Spline Random': 'C_OP_RampScalarSpline',
            'ease out': 'm_bEaseOut',
        'Remap Velocity to Vector': 'C_OP_RemapVelocityToVector',
            'normalize': 'm_bNormalize',
        'Ramp Scalar Spline Simple': 'C_OP_RampScalarSplineSimple',
            'ramp rate': 'm_Rate',
        'Ramp Scalar Linear Simple': 'C_OP_RampScalarLinearSimple',
            'end time': '',
        'Noise Vector': 'C_OP_VectorNoise',
            'noise coordinate scale': 'm_fl4NoiseScale',
            # m_bAdditive m_bOffset m_flNoiseAnimationTimeScale
        'Set Control Point To Player': PreOP('C_OP_SetControlPointToPlayer'),
            'Control Point Number': 'm_nCP1',
            'Control Point Offset': 'm_vecCP1Pos',
            # m_bOrientToEyes
        'Oscillate Scalar Simple': 'C_OP_OscillateScalarSimple',
            'oscillation rate': 'm_Rate',
            'oscillation frequency': 'm_Frequency',
        'Normal Lock to Control Point': 'C_OP_CalculateVectorAttribute',
        'Inherit Attribute From Parent Particle': 'C_OP_InheritFromParentParticlesV2',
            'Inherited Field': 'm_nFieldOutput',
        'Movement Lock to Saved Position Along Path': 'C_OP_LockToSavedSequentialPathV2',
            'Use sequential CP pairs between start and end point': 'm_bCPPairs',
            **_m_PathParams,
        'Restart Effect after Duration': 'C_OP_RestartAfterDuration',
            'Minimum Restart Time': '',
            'Maximum Restart Time': '',
        'Set per child control point from particle positions': 'C_OP_SetPerChildControlPoint',
            'control point to set': '',
            '# of children to set': 'm_nChildren', # made up
        'Remap Percentage Between Two Control Points to Scalar': 'C_OP_PercentageBetweenCPs',
            'treat distance between points as radius': '',
            'percentage maximum': '',
            'percentage minimum': '',
        'Remap Direction to CP to Vector': 'C_OP_RemapDirectionToCPToVector',
            'scale factor': '',
            'offset rotation': '',
            'offset axis': '',
        'Lerp Initial Scalar': 'C_OP_LerpScalar',
            'value to lerp to': '',
            'start time': '',
        'Lifespan Minimum Alpha Decay': 'C_OP_AlphaDecay',
            'minimum alpha': '',
        'Clamp Scalar': 'C_OP_ClampScalar',
        'Set Control Point Rotation': PreOP('C_OP_SetControlPointRotation'),
            'Rotation Rate': dynamicparam('m_flRotRate'),
            'Rotation Axis': dynamicparam('m_vecRotAxis'),
            'Local Space Control Point': 'm_nLocalCP',
        'Lifespan Minimum Radius Decay': 'C_OP_RadiusDecay',
        'Set control points from particle positions': 'C_OP_SetControlPointsToParticle',
        'Alpha Fade and Decay for Tracers': 'C_OP_FadeAndKillForTracers',
        'Noise Scalar': 'C_OP_Noise',
        'Rotation Orient to 2D Direction': 'C_OP_OrientTo2dDirection',
        'Rotate Vector Random': 'C_OP_RotateVector',
            'Rotation Rate Min': '',
            'Rotation Rate Max': '',
        'Movement Rotate Particle Around Axis': 'C_OP_MovementRotateParticleAroundAxis',
            'Use Local Space': 'm_bLocalSpace',
        'Remap Distance to Control Point to Vector': NotImplemented, # maybe C_OP_RemapDistanceToLineSegmentToVector
        'Distance to Control Points Scale': NotImplemented,
    }),

    'initializers': ('m_Initializers', {
        'Position Within Sphere Random': 'C_INIT_CreateWithinSphere',
            'speed_max': 'm_fSpeedMax',
            'speed_min': 'm_fSpeedMin',
            'distance_min': 'm_fRadiusMin',
            'distance_max': 'm_fRadiusMax',
            'speed_in_local_coordinate_system_max': 'm_LocalCoordinateSystemSpeedMax',
            'speed_in_local_coordinate_system_min': 'm_LocalCoordinateSystemSpeedMin',
            'distance_bias': 'm_vecDistanceBias',
            'distance_bias_absolute_value': 'm_vecDistanceBiasAbs',
            'speed_random_exponent': 'm_fSpeedRandExp',
            'control_point_number': 'm_nControlPointNumber',
            'bias in local system': 'm_bLocalCoords',
            'randomly distribute to highest supplied Control Point': Discontinued(10),
            'randomly distribution growth time': 'm_flEndCPGrowthTime',
            'scale cp (distance/speed/local speed)': 'm_nScaleCP',
            'create in model': Discontinued(),

        'Move Particles Between 2 Control Points': 'C_INIT_MoveBetweenPoints',
        'move particles between 2 control points': 'C_INIT_MoveBetweenPoints',
            'start offset': 'm_flStartOffset',
            'end offset': 'm_flEndOffset',
            'maximum speed': 'm_flSpeedMax',
            'minimum speed': 'm_flSpeedMin',
            'end spread': 'm_flEndSpread',
            'end control point': 'm_nEndControlPointNumber',
        '': '',
        '': '',
        '': '',
        '': '',
        '': '',
        'Lifetime Random': 'C_INIT_RandomLifeTime',
        'lifetime_random': 'C_INIT_RandomLifeTime',
            'lifetime_min': 'm_fLifetimeMin',
            'lifetime_max': 'm_fLifetimeMax',
            'lifetime_random_exponent': 'm_fLifetimeRandExponent',

        'Color Random': 'C_INIT_RandomColor',
        'color_random': 'C_INIT_RandomColor',
            'tint clamp max': 'm_TintMax',
            'tint clamp min': 'm_TintMin',
            'tint update movement threshold': 'm_flUpdateThreshold',
            'light amplification amount': 'm_flLightAmplification',
            'color1': 'm_ColorMin',
            'color2': 'm_ColorMax',
            'tint_perc': 'm_flTintPerc',
            'tint blend mode': 'm_nTintBlendMode',
            'tint control point': 'm_nTintCP',

        'Rotation Random': 'C_INIT_RandomRotation',
        'rotation_random': 'C_INIT_RandomRotation',
        'random_rotation': 'C_INIT_RandomRotation',
            'randomly_flip_direction': 'm_bRandomlyFlipDirection',
            'rotation_offset_max': 'm_flDegreesMax',
            'rotation_offset_min': 'm_flDegreesMin',
            'rotation_initial': 'm_flDegrees',
            'rotation_random_exponent': 'm_flRotationRandExponent',
            #'rotation_field': 'm_nFieldOutput',

        'Alpha Random': 'C_INIT_RandomAlpha',
        'alpha_random': 'C_INIT_RandomAlpha',
            #'alpha_field': 'm_nFieldOutput',
            'alpha_max': 'm_nAlphaMin',
            'alpha_min': 'm_nAlphaMax',
            'alpha_random_exponent': 'm_flAlphaRandExponent',
            'run for killed parent particles': Discontinued(),

        'Position Modify Offset Random': 'C_INIT_PositionOffset',
        'position_offset_random': 'C_INIT_PositionOffset',
            'offset max': 'm_OffsetMin',
            'offset min': 'm_OffsetMax',
            'offset in local space 0/1': 'm_bLocalCoords',
            'offset proportional to radius 0/1': 'm_bProportional',

        'Sequence Random': 'C_INIT_RandomSequence',
        'sequence_random': 'C_INIT_RandomSequence',
            'sequence_max': 'm_nSequenceMax',
            'sequence_min': 'm_nSequenceMin',
            'shuffle': 'm_bShuffle',
            'linear': 'm_bLinear',

        'Sequence Two Random': 'C_INIT_RandomSecondSequence',
        'Radius Random': 'C_INIT_RandomRadius',
        'radius_random': 'C_INIT_RandomRadius', # gotta love multiple names
        'random_radius': 'C_INIT_RandomRadius',
            'radius_min': 'm_flRadiusMin',
            'radius_max': 'm_flRadiusMax',
            'radius_random_exponent': 'm_flRadiusRandExponent',

        'Rotation Speed Random': 'C_INIT_RandomRotationSpeed',
            'rotation_speed_random_min': 'm_flDegreesMin',
            'rotation_speed_random_max': 'm_flDegreesMax',
            'rotation_speed_constant': 'm_flDegrees',#Discontinued(), # unsure
            'rotation_speed_random_exponent': 'm_flRotationRandExponent',
            # m_bRandomlyFlipDirection

        'Position Within Box Random': 'C_INIT_CreateWithinBox',
        'position_within_box': 'C_INIT_CreateWithinBox',
            'max': 'm_vecMax',
            'min': 'm_vecMin',
            'use local space': 'm_bLocalSpace',

        'Rotation Yaw Flip Random': 'C_INIT_RandomYawFlip',
        'Randomly Flip Yaw': 'C_INIT_RandomYawFlip', # are these the same?
            'Flip Percentage': 'm_flPercent',

        'remap initial scalar': 'C_INIT_RemapScalar',
            'input minimum': 'm_flInputMin',
            'input maximum': 'm_flInputMax',
            'output minimum': 'm_flOutputMin',
            'output maximum': 'm_flOutputMax',
            'output is scalar of initial random range': BoolToSetKV('m_nSetMethod', 'PARTICLE_SET_SCALE_INITIAL_VALUE'), # unsure
            'output field': 'm_nFieldOutput', # "{val}" in vpcf?
            'input field': 'm_nFieldInput',

        'Position Modify Warp Random': 'C_INIT_PositionWarp',
            'warp min': 'm_vecWarpMin',
            'warp max': 'm_vecWarpMax',
            'warp transition time (treats min/max as start/end sizes)': 'm_flWarpTime',
            'warp transition start time': 'm_flWarpStartTime',
            'reverse warp (0/1)': 'm_bInvertWarp',
            'use particle count instead of time': 'm_bUseCount',
            'local coordinate space': Discontinued(),

            # m_nScaleControlPointNumber m_nRadiusComponent m_flPrevPosScale
        'Velocity Noise': 'C_INIT_InitialVelocityNoise',
        'Initial Velocity Noise': 'C_INIT_InitialVelocityNoise',
            'Time Noise Coordinate Scale': dynamicparam('m_flNoiseScale'),
            'Spatial Noise Coordinate Scale': dynamicparam('m_flNoiseScaleLoc'),
            'Absolute Value': 'm_vecAbsVal',
            'Apply Velocity in Local Space (0/1)': 'm_bLocalSpace',
            'Invert Abs Value': 'm_vecAbsValInv',
            'Spatial Coordinate Offset': dynamicparam('m_vecOffsetLoc'),
            'Time Coordinate Offset': dynamicparam('m_flOffset'),
            'Control Point Number': 'm_nControlPointNumber',

        'Trail Length Random': 'C_INIT_RandomTrailLength',
        'trail_length_random': 'C_INIT_RandomTrailLength',
            'length_min': 'm_flMinLength',
            'length_max': 'm_flMaxLength',
            'length_random_exponent': 'm_flLengthRandExponent',

        'Lifetime From Sequence': 'C_INIT_SequenceLifeTime',
        'lifetime from sequence': 'C_INIT_SequenceLifeTime',
            'Frames Per Second': 'm_flFramerate',

        'Remap Initial Scalar': 'C_INIT_RemapScalar', # 'remap initial scalar' duplicate wtf
            'emitter lifetime end time (seconds)': 'm_flStartTime',
            'emitter lifetime start time (seconds)': 'm_flEndTime',
            'only active within specified input range': 'm_bActiveRange',

        'Remap Initial Distance to Control Point to Scalar': 'C_INIT_DistanceToCPInit',
            'distance minimum': 'm_flInputMin',
            'distance maximum': 'm_flInputMax',
            'control point': 'm_nStartCP',
            'only active within specified distance': 'm_bActiveRange',
            'LOS Failure Scalar': 'm_flLOSScale',
            'Maximum Trace Length': 'm_flMaxTraceLength',
            'LOS collision group': 'm_CollisionGroupName',
            'ensure line of sight': 'm_bLOS',
        'Position Along Ring': 'C_INIT_RingWave',
        'initialize_within_sphere': 'C_INIT_RingWave', # is it?
            'initial radius': 'm_flInitialRadius',
            'thickness': 'm_flThickness',
            'min initial speed': 'm_flInitialSpeedMin',
            'max initial speed': 'm_flInitialSpeedMax',
            'even distribution': 'm_bEvenDistribution',
            'XY velocity only': 'm_bXYVelocityOnly',
            'even distribution count': 'm_flParticlesPerOrbit',
            'control point number': 'm_nControlPointNumber',
            'Override CP (X/Y/Z *= Radius/Thickness/Speed)': 'm_nOverrideCP',
            'pitch': 'm_flPitch',
            'yaw': 'm_flYaw',
            'roll': 'm_flRoll',
            # m_nOverrideCP2
        'Velocity Random': 'C_INIT_VelocityRandom',
            'random_speed_max': dynamicparam('m_fSpeedMax'),
            'random_speed_min': dynamicparam('m_fSpeedMin'),
            # this one has got 'speed_in_local_coordinate_system_min', etc from C_INIT_CreateWithinSphere random
            # but on this one its a dynamicparam, so can you skip dynamic paraming on this (and most that dont use random) #TODO
        'Position From Parent Particles': 'C_INIT_CreateFromParentParticles',
            'Inherited Velocity Scale': 'm_flVelocityScale',
            'Random Parent Particle Distribution': 'm_bRandomDistribution',
            # m_flIncrement = 11.0 m_bRandomDistribution = true m_nRandomSeed = 1 m_bSubFrame = false
        'Remap Scalar to Vector': 'C_INIT_RemapScalarToVector',
        'remap scalar to vector': 'C_INIT_RemapScalarToVector',
            'use local system': 'm_bLocalCoords',
        'Scalar Random': 'C_INIT_RandomScalar',
        'Initial Scalar Noise': 'C_INIT_RandomScalar', # is this scalar random?
            # this likely has m_flMin & clashes with m_vecMin TODO FIXME
        'Remap Control Point to Scalar': 'C_INIT_RemapCPtoScalar',
            'input control point number': 'm_nCPInput',
            'input field 0-2 X/Y/Z': 'm_nField',
        'Position on Model Random': 'C_INIT_CreateOnModel',
        'random position on model': 'C_INIT_CreateOnModel',
            'force to be inside model': 'm_nForceInModel',
            'direction bias': 'm_vecDirectionBias',
            'bias in local space': 'm_bLocalCoords',
            'model hitbox scale': 'm_flHitBoxScale',
            'hitbox scale': 'm_flHitBoxScale',
            'desired hitbox': 'm_nDesiredHitbox',
            # m_nHitboxValueFromControlPointIndex m_bUseBones m_flBoneVelocity 'inherited' m_flMaxBoneVelocity
        'Velocity Set from Control Point': 'C_INIT_VelocityFromCP',
        'Position Modify Place On Ground': 'C_INIT_PositionPlaceOnGround',
            'collision group': 'm_CollisionGroupName',
            'max trace length': 'm_flMaxTraceLength',
            'kill on no collision': 'm_bKill',
            'offset': 'm_flOffset',
            'set normal': 'm_bSetNormal',
            'include water': 'm_bIncludeWater',
        'Velocity Inherit from Control Point': 'C_INIT_InheritVelocity',
        'Inherit Velocity': 'C_INIT_InheritVelocity',
            'velocity scale': 'm_flVelocityScale',
        'Remap Noise to Scalar': 'C_INIT_CreationNoise',
            'time noise coordinate scale': 'm_flNoiseScale',
            'spatial noise coordinate scale': 'm_flNoiseScaleLoc',
            'world time noise coordinate scale': 'm_flWorldTimeScale',
            'time coordinate offset': 'm_flOffset',
            'spatial coordinate offset': 'm_vecOffsetLoc',
            'absolute value': 'm_bAbsVal',
            'invert absolute value': 'm_bAbsValInv',
        'Lifetime Pre-Age Noise': 'C_INIT_AgeNoise',
            'start age minimum': 'm_flAgeMin',
            'start age maximum': 'm_flAgeMax',
        'Position In CP Hierarchy': '', # suspect C_INIT_CreateFromCPs maybe needs processing
        'Lifetime from Time to Impact': 'C_INIT_LifespanFromVelocity',
            'maximum trace length': 'm_flMaxTraceLength',
            'trace collision group': 'm_CollisionGroupName',
            'trace offset': 'm_flTraceOffset',
            'trace recycle tolerance': 'm_flTraceTolerance',
            'maximum points to cache': 'm_nMaxPlanes',
            'bias distance': 'm_vecComponentScale',
            # m_bIncludeWater = false
        'Position from Parent Cache': ('C_INIT_CreateFromPlaneCache', {
            'Local Offset Max': 'm_vecOffsetMax',
            'Local Offset Min': 'm_vecOffsetMin',
            'Set Normal': 'm_bUseNormal', #that clashes with another m_bSetNormal
        }),
        'Rotation Yaw Random': 'C_INIT_RandomYaw',
            'yaw_offset_min': 'm_flDegreesMin',
            'yaw_offset_max': 'm_flDegreesMax',
            'yaw_random_exponent': 'm_flRotationRandExponent',
            'yaw_initial': 'm_flDegrees',
        'Position Along Path Sequential': 'C_INIT_CreateSequentialPathV2', # wonder what happened to v1
        'sequential position along path': 'C_INIT_CreateSequentialPathV2',
            'particles to map from start to end': 'm_flNumToAssign',
            'maximum distance': 'm_fMaxDistance',
            'restart behavior (0 = bounce, 1 = loop )': 'm_bLoop',
            'Use sequential CP pairs between start and end point': 'm_bCPPairs',
            'Save Offset': 'm_bSaveOffset',
            **_m_PathParams,
            # m_vStartPointOffset m_vMidPointOffset m_vEndOffset
        'Velocity Repulse from World': 'C_INIT_InitialRepulsionVelocity',
            'Trace Length': 'm_flTraceLength',
            'Inherit from Parent': 'm_bInherit',
            'minimum velocity': 'm_vecOutputMin',
            'maximum velocity': 'm_vecOutputMax',
            'control points to broadcast to children (n + 1)': 'm_nChildCP',
            'Offset instead of accelerate': 'm_bTranslate',
            'Per Particle World Collision Tests': 'm_bPerParticle',
            'Use radius for Per Particle Trace Length': 'm_bPerParticleTR',
            'Offset proportional to radius 0/1': 'm_bProportional',
            'Child Group ID to affect': 'm_nChildGroupID',
        'Cull relative to Ray Trace Environment': 'C_INIT_RtEnvCull',
            #'test direction': 'm_vecTestDir',
            'cull on miss': 'm_bCullOnMiss',
            'cull normal': 'm_vecTestNormal',
            'ray trace environment name': 'm_RtEnvName',
            'velocity test adjust lifespan': 'm_bLifeAdjust',
            'use velocity for test direction': 'm_bUseVelocity',
        'Color Lit Per Particle': 'C_INIT_ColorLitPerParticle',
            'light bias': 'm_flTintPerc',
            'position_within_sphere': Discontinued(),
        'Position Along Path Random': 'C_INIT_CreateAlongPath',
            'randomly select sequential CP pairs between start and end points': '',
            **_m_PathParams,
        'Remap Particle Count to Scalar': 'C_INIT_RemapParticleCountToScalar',
        'Remap Control Point to Vector': 'C_INIT_RemapCPtoVector',
        'remap control point to Vector': 'C_INIT_RemapCPtoVector',
            'offset position': 'm_bOffset',
            'accelerate position': 'm_bAccelerate',
            'local space CP': 'm_nLocalSpaceCP',
        'Normal Modify Offset Random': 'C_INIT_NormalOffset',
            'normalize output 0/1': 'm_bNormalize',
        'CP Scale Size': '', # Discontinued / NotImplemented
        'CP Scale Life': '',
        'CP Scale Trail': '',
        'Position Along Epitrochoid': 'C_INIT_CreateInEpitrochoid',
            'offset from existing position': 'm_bOffsetExistingPos',
            'use particle count instead of creation time': 'm_bUseCount',
            'particle density': 'm_flParticleDensity',
            'point offset': 'm_flOffset',
            'radius 2': 'm_flRadius2',
            'radius 1': 'm_flRadius1',
            'first dimension 0-2 (-1 disables)': 'm_nComponent1',
            'second dimension 0-2 (-1 disables)': 'm_nComponent2',
            # m_bUseLocalCoords m_nScaleCP m_nControlPointNumber
        'Movement Follow CP': '',
            'update particle life time': '',
            'lerp to CP radius speed': '',
            'catch up speed': '',
            'maximum end control point': '',
        'Random position within a curved cylinder': 'C_INIT_CreateInCurvedCylinder', # made up
            'starting control point for cylinder': '',
            'maximum end control point for cylinder': '',
            'min scale factor for mapping cp velocity to particle velocity': '',
            'max scale factor for mapping cp velocity to particle velocity': '',
            'min scale factor for particle velocity along path': '',
            'max scale factor for particle velocity along path': '',
        'Normal Align to CP': 'C_INIT_NormalAlignToCP',
        'Assign target CP': '',
        'Lifetime From Control Point Life Time': Discontinued(),
        'Remap Speed to Scalar': 'C_INIT_RemapSpeedToScalar',
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
            'emission count scale control point': '',
            'emission count scale control point field': '',
            'maximum emission per frame': 'm_nMaxEmittedPerFrame',
            # _nParticlesToEmit =
            # {
            # 	m_nType = "PF_TYPE_RANDOM_UNIFORM"
            # 	m_flRandomMin = 80.0
            # 	m_flRandomMax = 160.0
            # 	m_nRandomMode = "PF_TYPE_RANDOM_UNIFORM" # not needed i think
            # }
            # probably modified? why did you do this mr csgo dev
            # "num_to_emit" "int" "180"
            # "num_to_emit_minimum" "int" "100"
            'num_to_emit_minimum': minof('m_nParticlesToEmit'),

        }),
        'emit_continuously': ('C_OP_ContinuousEmitter', {
            'emission_duration': dynamicparam('m_flEmissionDuration'),
            'emission_rate': dynamicparam('m_flEmitRate'),
            'emission_start_time': dynamicparam('m_flStartTime'),
            'emission count scale control point': 'm_nScaleControlPoint',
            'emission count scale control point field': 'm_nScaleControlPointField',
            'scale emission to used control points': Discontinued(10),
            'use parent particles for emission scaling': 'm_flScalePerParentParticle',
            'emit particles for killed parent particles': 'm_bInitFromKilledParentParticles',
        }),
        'emit noise': ('C_OP_NoiseEmitter', {
            'emission_start_time': 'm_flStartTime',
            'emission_duration': 'm_flEmissionDuration',
            'scale emission to used control points': 'm_nScaleControlPoint',
            'time noise coordinate scale': 'm_flNoiseScale',
            'time coordinate offset': 'm_flOffset',
            'absolute value': 'm_bAbsVal',
            'invert absolute value': 'm_bAbsValInv',
            'emission minimum': 'm_flOutputMin',
            'emission maximum': 'm_flOutputMax',
            'world time noise coordinate scale': 'm_flWorldTimeScale',

        }),
        'emit to maintain count': ('C_OP_MaintainEmitter', {
            'count to maintain': 'm_iMaintainCount',
            'maintain count scale control point': 'm_nScaleControlPoint',
        }),
    }),
    'forces': ('m_ForceGenerators', {
        'twist around axis': ('C_OP_TwistAroundAxis', {
            'amount of force': 'm_fForceAmount',
            'twist axis': 'm_TwistAxis',
            'object local space axis 0/1': 'm_bLocalSpace',
        }),
        'random force': ('C_OP_RandomForce', {
            'min force': 'm_MinForce',
            'max force': 'm_MaxForce',
        }),
        'Force based on distance from plane': ('C_OP_ForceBasedOnDistanceToPlane', {
            'Max Distance from plane': 'm_flMaxDist',
            'Force at Max distance': 'm_vecForceAtMaxDist',
            'Exponent': 'm_flExponent',
            'Plane Normal': 'm_vecPlaneNormal',
            'Control point number': 'm_nControlPointNumber',
            'Min distance from plane': 'm_flMinDist',
            'Force at Min distance': 'm_vecForceAtMinDist',

        }),
        'time varying force': ('C_OP_TimeVaryingForce', {
            'time to start transition': 'm_flStartLerpTime',
            'starting force': 'm_StartingForce',
            'time to end transition': 'm_flEndLerpTime',
            'ending force': 'm_EndingForce',
        }),
        'Pull towards control point': ('C_OP_AttractToControlPoint', {
            'amount of force': dynamicparam('m_fForceAmount'),
            'falloff power': 'm_fFalloffPower',
            'control point number': 'm_nControlPointNumber',
        }),
         'turbulent force': ('C_OP_TurbulenceForce', {
            'Noise scale 0': 'm_flNoiseCoordScale0',
            'Noise scale 1': 'm_flNoiseCoordScale1',
            'Noise scale 2': 'm_flNoiseCoordScale2',
            'Noise scale 3': 'm_flNoiseCoordScale3',
            'Noise amount 0': 'm_vecNoiseAmount0',
            'Noise amount 1': 'm_vecNoiseAmount1',
            'Noise amount 2': 'm_vecNoiseAmount2',
            'Noise amount 3': 'm_vecNoiseAmount3',
        }),
        'lennard jones force': NotImplemented,
        'up': NotImplemented,
        'down': NotImplemented,
   }),

    'constraints': ('m_Constraints', {
        'Constrain distance to control point': ('C_OP_ConstrainDistance', {
            'minimum distance': 'm_fMinDistance',
            'maximum distance': 'm_fMaxDistance',
            'offset of center': 'm_CenterOffset',
            'control point number': 'm_nControlPointNumber',
            '': 'm_nScaleCP',
            'global center point': 'm_bGlobalCenter',
        }),
        'Prevent passing through a plane': ('C_OP_PlanarConstraint', {
            'plane point': 'm_PointOnPlane',
            'plane normal': 'm_PlaneNormal',
            'control point number': 'm_nControlPointNumber',
            'global normal': 'm_bGlobalNormal',
            'global origin': 'm_bGlobalOrigin',
            # m_PointOnPlane m_PlaneNormal dynamicparam('m_flRadiusScale') dun(m_flMaximumDistanceToCP)
        }),
        'Collision via traces': ('C_OP_WorldTraceConstraint', {
            'trace accuracy tolerance': 'm_flTraceTolerance',
            'collision group': 'm_CollisionGroupName', # s2defval = 'NONE'
            'amount of slide': dynamicparam('m_flSlideAmount'),
            'amount of bounce': dynamicparam('m_flBounceAmount'),
            'collision mode': remap('m_nCollisionMode', map = {
                0: 'COLLISION_MODE_PER_PARTICLE_TRACE',
                1: 'COLLISION_MODE_USE_NEAREST_TRACE',
                2: 'COLLISION_MODE_PER_FRAME_PLANESET',
                3: 'COLLISION_MODE_INITIAL_TRACE_DOWN',
            }),
            'radius scale': 'm_flRadiusScale',
            'brush only': 'm_bBrushOnly', # brushes yes?
            'Confirm Collision': 'm_flCollisionConfirmationSpeed',
            'control point movement distance tolerance': 'm_flCpMovementTolerance',
            'minimum speed to kill on collision': 'm_flMinSpeed',
            'kill particle on collision': 'm_bKillonContact',
            'control point offset for fast collisions': 'm_vecCpOffset',
            'trace accuracy tolerance': 'm_flTraceTolerance',
            'control point': 'm_nCP',
        }),
        'Constrain distance to path between two control points': ('', {
            'minimum distance': 'm_fMinDistance',
            'maximum distance': 'm_flMaxDistance0',
            'maximum distance middle': 'm_flMaxDistanceMid',
            'maximum distance end': 'm_flMaxDistance1',
            'travel time': 'm_flTravelTime',
            'random bulge': ObjectP('m_PathParameters', 'm_flBulge'),
            **_m_PathParams,
        }),
        'Constrain particles to a box': ('C_OP_BoxConstraint', {
            'min coords': 'm_vecMin',
            'max coords': 'm_vecMax',
            '':"""
			m_nCP = 4
			m_bLocalSpace = true"""
        }),
        'Prevent passing through static part of world':'C_OP_WorldCollideConstraint',
    }),

    '__renderer_shared': {
        'Visibility Proxy Radius': ObjectP(_vi:='VisibilityInputs', 'm_flProxyRadius'),
        'Visibility input minimum':  ObjectP(_vi,           'm_flInputMin'),
        'Visibility input maximum':  ObjectP(_vi,           'm_flInputMax'),
        'Visibility input dot minimum': ObjectP(_vi,        'm_flDotInputMin'),
        'Visibility input dot maximum': ObjectP(_vi,        'm_flDotInputMax'),
        'Visibility input distance minimum': ObjectP(_vi,   'm_flDistanceInputMin'),
        'Visibility input distance maximum': ObjectP(_vi,   'm_flDistanceInputMax'),
        'Visibility Alpha Scale minimum': ObjectP(_vi,      'm_flAlphaScaleMin'),
        'Visibility Alpha Scale maximum': ObjectP(_vi,      'm_flAlphaScaleMax'),
        'Visibility Radius Scale minimum': ObjectP(_vi,     'm_flRadiusScaleMin'),
        'Visibility Radius Scale maximum': ObjectP(_vi,     'm_flRadiusScaleMax'),
        'Visibility Radius FOV Scale base': ObjectP(_vi,    'm_flRadiusScaleFOVBase'),
        'Visibility Proxy Input Control Point Number': ObjectP(_vi, 'm_nCPin'),
    },
    '__operator_shared': {
        'operator start fadein': 'm_flOpStartFadeInTime',
        'operator end fadein': 'm_flOpEndFadeInTime',
        'operator start fadeout': 'm_flOpStartFadeOutTime',
        'operator end fadeout': 'm_flOpEndFadeOutTime',
        'operator fade oscillate': 'm_flOpFadeOscillatePeriod',
        'normalize fade times to endcap': 'm_bNormalizeToStopTime',
        'operator time scale min': 'm_flOpTimeScaleMin',
        'operator time scale max': 'm_flOpTimeScaleMax',
        'operator time scale seed': 'm_nOpTimeScaleSeed',
        'operator time offset min': 'm_flOpTimeOffsetMin',
        'operator time offset max': 'm_flOpTimeOffsetMax',
        'operator time offset seed': 'm_flOpTimeOffsetSeed',
        'operator end cap state': 'm_nOpEndCapState',
        'operator strength random scale min': minof('m_flOpStrength'),
        'operator strength random scale max': maxof('m_flOpStrength'),
        'operator time strength random scale max': '',
        'operator strength scale seed': '',

    },

    'children': ('m_Children', {
        'child': Ref('m_ChildRef'),
        'delay': 'm_flDelay',
        'end cap effect': 'm_bEndCap',

    }),
    'material': '',#Ref('m_hMaterial')

    # base properties
    'batch particle systems': 'm_bShouldBatch',
    'aggregation radius': 'm_flAggregateRadius',
    'view model effect': 'm_bViewModelEffect',
    'screen space effect': 'm_bScreenSpaceEffect',
    'maximum time step': 'm_flMaximumTimeStep',
    'minimum rendered frames': 'm_nMinimumFrames',
    'minimum simulation time step': 'm_flMinimumTimeStep',
    'freeze simulation after time': 'm_flStopSimulationAfterTime', # s2def "1e+09"
    'maximum sim tick rate': 'm_flMaximumSimTime',
    'minimum sim tick rate': 'm_flMinimumSimTime',
    'rotation_speed': 'm_flConstantRotationSpeed',
    'cull_radius': 'm_flCullRadius',
    'control point to disable rendering if it is the camera': 'm_nSkipRenderControlPoint',
    'control point to only enable rendering if it is the camera': 'm_nAllowRenderControlPoint',
    'sequence_number': 'm_nConstantSequenceNumber',
    'sequence_number 1': 'm_nConstantSequenceNumber1',
    'minimum free particles to aggregate': 'm_nAggregationMinAvailableParticles',
    'rotation': 'm_flConstantRotation',
    'group id': 'm_nGroupID',
    'cull_cost': 'm_flCullFillCost',
    'minimum CPU level': 'm_nMinCPULevel',
    'minimum GPU level': 'm_nMinGPULevel',
    'cull_control_point': 'm_nCullControlPoint',
    'normal': 'm_ConstantNormal',
    'max_particles':                    'm_nMaxParticles',
    'initial_particles':                'm_nInitialParticles',
    'snapshot':                         Ref('m_hSnapshot'),
    'cull_replacement_definition':      Ref('m_pszCullReplacementName'),
    'fallback replacement definition':  Ref('m_hFallback'),    
    'fallback max count':               'm_nFallbackMaxCount',
    'radius':                           'm_flConstantRadius',
    'color':                            'm_ConstantColor',
    'maximum draw distance':            'm_flMaxDrawDistance',
    'time to sleep when not drawn':     'm_flNoDrawTimeToGoToSleep',
    'Sort particles':                   'm_bShouldSort', # deprecated use renderer m_nSortMethod "0"
    'bounding_box_min':                 'm_BoundingBoxMin',
    'bounding_box_max':                 'm_BoundingBoxMax',
    'tintr': SingleColour('m_ConstantColor', 1),
    'tintg': SingleColour('m_ConstantColor', 2),
    'tintb': SingleColour('m_ConstantColor', 3),
    'bounding_box_control_point': '',
    'maximum portal recursion depth': '',
    'fallback_dx80': '',
    'draw through leafsystem': '',
    'preventNameBasedLookup': '',

}

NotFoundYet = ''

class fx:
    "`self.func` is the func that will be applied to the value"
    def __init__(self, t: str, func):
        self.t = t
        self.func = func

# out of scale textures on fountain rings...
# is this same as hammer texture scale issue
# vtf scaling -> m_flConstantRadius
# vistasmokev1_emods.vmt ->
# vistasmokev1_emods.mks | vistasmokev1_emods.txt(empty) | [pieces]
vmt_to_vpcf = {
    # https://developer.valvesoftware.com/wiki/SpriteCard
    # https://developer.valvesoftware.com/wiki/Refract

    '$vertexcolor': 'm_bPerVertexLighting',
    '$minsize': 'm_flMinSize',
    '$maxsize': 'm_flMaxSize',
    '$minfadesize': dynamicparam('m_flStartFadeSize'),
    '$maxfadesize': dynamicparam('m_flEndFadeSize'),
    '$startfadesize': '',
    '$endfadesize': '',
    '$farfadeinterval': '',

    '$blendframes': 'm_bBlendFramesSeq0',
    '$zoomanimateseq2': 'm_flZoomAmount1',
    '$sequence_blend_mode': remap('m_nSequenceCombineMode', map = {
        0: 'SEQUENCE_COMBINE_MODE_AVERAGE',
        1: 'SEQUENCE_COMBINE_MODE_ALPHA_FROM0_RGB_FROM_1',
        2: 'SEQUENCE_COMBINE_MODE_ADDITIVE',
    }),
    '$maxlumframeblend1': 'm_bMaxLuminanceBlendingSequence0',
    '$maxlumframeblend2': 'm_bMaxLuminanceBlendingSequence1',
    '$addself': 'm_flAddSelfAmount',

    #'$inversedepthblend': '', # m_bReverseZBuffering
    '$spriteorientation': remap('m_nOrientationType', map = {
        'vp_parallel': 0
    }),
    '$spriterendermode': BoolToSetKV('m_nColorBlendType', "PARTICLE_COLOR_BLEND_ADD"), # temp
    '$orientation': 'm_nOrientationType',
    '$orientationmatrix': '',
    '$alpha': dynamicparam('m_flAlphaScale'),
    '$translucent': '', # Enable expensive translucency
    '$nocull': '',
    '$mod2x': 'm_bMod2X',
    '$additive': 'm_bAdditive', # color blend type ?
    '$opaque': 'm_bDrawAsOpaque',
    '$ignorez': 'm_bDisableZBuffering',
    '$inversedepthblend': '', # sort method oldest?
    '$nofog': lambda v: ('m_bFogParticles',not v),
    '$overbrightfactor': lambda v: ('m_flOverbrightFactor', v+1.0),
    '$distancealpha': 'm_bDistanceAlpha',
    '$softedges': 'm_bSoftEdges',
    '$edgesoftnessstart': 'm_flEdgeSoftnessStart',
    '$edgesoftnessend': 'm_flEdgeSoftnessEnd',
    '$outline': 'm_bOutline',
    '$outlinecolor': 'm_OutlineColor',
    '$outlinealpha': 'm_nOutlineAlpha',
    '$outlinestart0': 'm_flOutlineStart0',
    '$outlinestart1': 'm_flOutlineStart1',
    '$outlineend0': 'm_flOutlineEnd0',
    '$outlineend1': 'm_flOutlineEnd1',
    '$refractamount': 'm_flRefractAmount',
    '$bluramount': 'm_nRefractBlurRadius',
    '$cropfactor': '', # Texture UV control magic?
    '$pos': '', # subrect
    '$size': '', # subrect
    '$aimatcamera': '',

    #'$orientationmatrix' i think this needs a separate control point
    #'$basetexturetransform': (  'm_flFinalTextureScaleU',
    #                            'm_flFinalTextureScaleV',
    #                            'm_flFinalTextureOffsetU',
    #                            'm_flFinalTextureOffsetV',
    #                            'm_flCenterXOffset',
    #                            'm_flCenterYOffset'),
}
vmtshader = {
    'unlitgeneric': ('m_bGammaCorrectVertexColors', False),
    'sprite': '',
    'spritecard': '',
    'refract': 'm_bRefract',
    'decalmodulate': '',
    'subrect': '',
    'particlesphere': '',
    'splinerope': '',

}

explosions_fx = Path(r'D:\Users\kristi\Documents\GitHub\source1import\utils\shared\particles\explosions_fx.pcf')
lightning = Path(r'D:\Users\kristi\Documents\GitHub\source1import\utils\shared\particles\lighting.pcf')

particles_in = Path(r'D:\Games\steamapps\common\Half-Life Alyx\game\csgo\particles')
particles_out = Path(r'D:\Games\steamapps\common\Half-Life Alyx\content\hlvr_addons\csgo\particles')
#particles_out = Path(r'C:\Users\kristi\Desktop\Source 2\content\hlvr_addons\addon\particles')
def is_valid_pcf(x: dmx.DataModel):
    return ('particleSystemDefinitions' in x.elements[0].keys() and
            'DmeParticleSystemDefinition' == x.elements[1].type)

def guess_key_name(key, value):
    key_words = key.replace('_', ' ').split(' ')

    shorts = {'minimum':'min', 'maximum':'max', 'simulation':'sim', 'rotation':'rot', 'interpolation':'lerp'}
    typepreffix = {
        bool:'b', float:'fl', int:'n', Ref:'h'
    }

    guess = 'm_' + typepreffix.get(type(value), '')
    # TODO: list -> vec, ang, ''
    # TODO: fade_and_kill -> C_OP_FadeAndKill
    for kw in key_words[:3]:
        if kw.startswith('('):
            break
        elif '#' in kw or "'" in kw: break
        kw = shorts.get(kw, kw)
        guess += kw.capitalize()
    return guess, value

materials = set()
children = []
fallbacks = []

def process_material(value):
    if not value:
        return

    vmt_path = Path(PATH_TO_CONTENT_ROOT) / value
    vmat_path = Path('materials') / Path(value).with_suffix('.vmat')
    renderer_base['m_hMaterial'] = resource(vmat_path)
    try:
        vmt = VMT(KV.FromFile(vmt_path))
    except FileNotFoundError:
        materials.add(value)
    else:
        if (shader_add:=vmtshader.get(vmt.shader)) is not None:
            if not shader_add == '':
                if isinstance(shader_add, tuple):
                    renderer_base[shader_add[0]] = shader_add[1]
                else:
                    renderer_base[shader_add] = True
        else:
            un(vmt.shader, 'VMTSHADER')
        non_opaque_params = ('$addbasetexture2', '$dualsequence', '$sequence_blend_mode', '$maxlumframeblend1', '$maxlumframeblend2', '$extractgreenalpha', '$ramptexture', '$zoomanimateseq2', '$addoverblend', '$addself', '$blendframes', '$depthblend', '$inversedepthblend')
        if vmt.KeyValues.get('$opaque', 0) == 1:
            for nop in non_opaque_params:
                print('deleted', nop, vmt.KeyValues[nop])
                del vmt.KeyValues[nop]
                input(str(vmt.KeyValues))
        for vmtkey, vmtval in vmt.KeyValues.items():
            if '?' in vmtkey: vmtkey = vmtkey.split('?')[1]
            if vmtkey in ('$basetexture', '$material', '$normalmap', '$bumpmap'):
                vtex_ref = resource((Path('materials') / vmtval).with_suffix('.vtex'))
                vpcf_replacement_key = 'm_hTexture' if vmtkey in ('$basetexture', '$material') else 'm_hNormalTexture'
                renderer_base[vpcf_replacement_key] = vtex_ref
                continue
            if vmtkey not in vmt_to_vpcf:
                #un((vmtkey, vmtval), "VMT")
                continue
            add = vmt_to_vpcf[vmtkey]
            if callable(add):
                if isinstance(add, SingleColour):
                    add, vmtval = add(vmtval, existing = vpcf.get(add.t, add.default))
                else:
                    add, vmtval = add(vmtval)
            elif isinstance(add, tuple):
                add, vmtval = add
            if add:
                renderer_base[add] = vmtval
        # materials/particle/water/WaterSplash_001a.vtex


from materials_import import VMT, PATH_TO_CONTENT_ROOT
from shared.keyvalues1 import KV
def pcfkv_convert(key, value):

    if not (vpcf_translation:= pcf_to_vpcf.get(key)):
        if vpcf_translation is None:
            un(key, '_generic')
        return guess_key_name(key, value)
    elif vpcf_translation is NotImplemented:
        return

    outKey, outVal = key, value
    if key == 'snapshot': input(value)
    if isinstance(vpcf_translation, str):  # simple translation
        if value == []:
            return
        if isinstance(vpcf_translation, Ref):
            if not value:
                return
            return str(vpcf_translation), resource(Path(vpcf_localpath.parent / (value  + '.vpcf')))

        return vpcf_translation, value
    elif isinstance(vpcf_translation, tuple):
        if isinstance(vpcf_translation[1], str):  # insert to another dict
            return
        elif not isinstance(vpcf_translation[1], dict):
            return

        if not isinstance(value, list): # dmx._ElementArray
            print(key, "is not a list?", value)
            return
    
        outKey = vpcf_translation[0]
        outVal = []

        # convert the array
        for opitem in value:
            # handle the 2 formats
            # {'dmxobj': 'class', 'k':'kt'} <- this one has global subkeys
            # {'dmxobj': ('class', {'k':'kt'})}
            className = None
            sub_translation = vpcf_translation[1]
            if key != 'children':
                if (className := sub_translation.get(opitem.name)):
                    if type(className) is tuple:
                        className, sub_translation = className

                if not className:
                    if className is None:
                        un(opitem.name, outKey)
                    continue
                if className is NotImplemented:
                    continue

                
                subKV = { '_class': className}
                if key == 'renderers':
                    subKV.update(renderer_base)
            else:
                subKV = {}

            for key2, value2 in opitem.items():
                if key2 == 'functionName':
                    if value2 != opitem.name:
                        print("functionName mismatch", key2, opitem.name)
                    continue

                if not (subkey:=sub_translation.get(key2)):
                    if key2 in pcf_to_vpcf['__operator_shared']:
                        subkey = pcf_to_vpcf['__operator_shared'][key2]
                    elif key == 'renderers' and key2 in pcf_to_vpcf['__renderer_shared']:
                        subkey = pcf_to_vpcf['__renderer_shared'][key2]
                    else:
                        if subkey is None:
                            un(key2, opitem.name)
                        elif isinstance(subkey, Discontinued):
                            # if subkey.at >= vpcf m_nBehaviorVersion: # TODO,, also maybe this is not here __bool__ -> True
                            #     continue
                            continue
                        else:
                            subkey, value = guess_key_name(key2, value2)

                if not key2 or not subkey:
                    continue
                #if subkey == 'm_nCollisionMode' and (value2 == 1 or value2 == 2):
                #    print("YOOO", ParticleSystemDefinition.name)
                if isinstance(subkey, ObjectP):
                    subKV.setdefault(subkey.mother, {})[subkey.name] = value2
                    continue
                if isinstance(subkey, Ref):
                    if isinstance(value2, dmx.Element):
                        value2 = value2.name
                    else: input(f'Ref not an element {key2}: {value2}')
                    value2 = resource(Path(vpcf_localpath.parent / (value2  + '.vpcf')))
                elif isinstance(subkey, (minof, maxof)):
                    bMin = isinstance(subkey, minof)
                    if str(subkey) in subKV:
                        if not isinstance(subKV[subkey], dict): # not a dynamicparam
                            subKV[subkey] = dict(
                                m_nType = "PF_TYPE_RANDOM_UNIFORM",
                                m_flRandomMin = value2 if bMin else subKV[subkey],
                                m_flRandomMax = subKV[subkey] if bMin else value2
                            )
                        else:
                            if subKV[subkey].get('m_nType') == "PF_TYPE_LITERAL":
                                subKV[subkey]['m_nType'] = "PF_TYPE_RANDOM_UNIFORM"
                                subKV[subkey]['m_flRandomMax' if bMin else 'm_flRandomMin'] = subKV[subkey]['m_flLiteralValue']

                            subKV[subkey]['m_flRandomMin' if bMin else 'm_flRandomMax'] = value2
                        #if not bMin:
                        #    print(subKV[subkey]) # im seing 1.0 1.0 randoms!!
                        continue

                    else: value2 = dict(
                                m_nType = "PF_TYPE_RANDOM_UNIFORM",
                                m_flRandomMin = value2,
                                m_flRandomMax = value2
                            )
                elif isinstance(subkey, dynamicparam):
                    pass#value2 = {'m_nType': "PF_TYPE_LITERAL",'m_flLiteralValue': value2}
                elif isinstance(subkey, Multiple):
                    for bare_key in subkey.bare_replacements:
                        subKV[bare_key] = value2
                    for kk, f in subkey.kw_replacements.items():
                        subKV[kk] = f(value2)
                    continue
                elif callable(subkey):
                    if subkey is repr:
                        input("HEJ @",className, key2, value2)
                        continue
                    try:
                        subkey, value2 = subkey(value2)
                    except TypeError:
                        continue
                subKV[subkey] = value2

            outVal.append(subKV)
    else:
        return

    return outKey, outVal

class resource:
    def __init__(self, path):
        self.path = path
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}('{self.path!r}')"
    def __str__(self):
        return f'resource:"{self.path.as_posix()}"'

def dict_to_kv3_text(
        kv3dict: dict,
        header = '<!-- kv3 encoding:text:version{e21c7f3c-8a33-41c5-9977-a76d3a32aa0d} format:generic:version{7412167c-06e9-4698-aff2-e63eb59037e7} -->'
    ):
    kv3: str = header + '\n'

    def obj_serialize(obj, indent = 1, dictKey = False):
        preind = ('\t' * (indent-1))
        ind = ('\t' * indent)
        if obj is None:
            return 'null'
        elif isinstance(obj, bool):
            if obj: return 'true'
            return 'false'
        elif isinstance(obj, str):
            return '"' + obj + '"'
        elif isinstance(obj, list):
            s = '['
            if any(isinstance(item, dict) for item in obj):
                s = f'\n{preind}[\n'
                for item in obj:
                    s += (obj_serialize(item, indent+1) + ',\n')
                return s + preind + ']\n'

            return f'[{", ".join((obj_serialize(item, indent+1) for item in obj))}]'
        elif isinstance(obj, dict):
            s = preind + '{\n'
            if dictKey:
                s = '\n' + s
            for key, value in obj.items():
                #if value == [] or value == "" or value == {}: continue
                s +=  ind + f"{key} = {obj_serialize(value, indent+1, dictKey=True)}\n"
            return s + preind + '}'
        else: # likely an int, float
            # floats can be in e notation "1e+09"
            return str(obj)

    if not isinstance(kv3dict, dict):
        raise TypeError("Give me a dict, not this %s thing" % repr(kv3dict))
    kv3 += obj_serialize(kv3dict)

    return kv3

imports = []
unt = {}
def un(val, t):
    val, t = str(val), str(t)
    try:
        if t not in unt[val]:
            unt[val].append(t)
    except (KeyError, AttributeError):
        unt[val] = list()
        unt[val].append(t)

if __name__ == '__main__':
    for pcf_path in particles_in.glob('**/*.pcf'):
        #print(f"Reading particles/{pcf_path.name}")
        #if 'portal' in str(pcf_path):
        #    continue
        pcf = dmx.load(pcf_path)
        if not is_valid_pcf(pcf):
            print("Invalid!!")
            print(pcf.elements[0].keys())
            print(pcf.elements[1].type)
            continue

        vpcf_root = pcf_path.relative_to(particles_in).parent / pcf_path.stem
        (particles_out.parent / particles /vpcf_root).mkdir(parents = True, exist_ok=True)
        for ParticleSystemDefinition in pcf.find_elements(elemtype='DmeParticleSystemDefinition'):
            vpcf = dict(
                _class = "CParticleSystemDefinition",
                m_nBehaviorVersion = BEHAVIOR_VERSION
            )
            vpcf_localpath = particles / vpcf_root / (ParticleSystemDefinition.name + '.vpcf')
            vpcf_path = particles_out.parent / vpcf_localpath
            imports.append(vpcf_localpath.as_posix())
    
            renderer_base = {'m_bFogParticles': True}
            process_material(ParticleSystemDefinition.get('material'))

            for key, value in ParticleSystemDefinition.items():
                if converted_kv:= pcfkv_convert(key, value):
                    if not converted_kv[0]:
                        print('empty on', key, value)
                    vpcf[converted_kv[0]] = converted_kv[1]

            for operator in vpcf.get('m_Operators', ()):
                if not operator.get('_class') in vpcf_PreOPs:
                    continue
                vpcf['m_Operators'].remove(operator)
                vpcf.setdefault('m_PreEmissionOperators', list())
                vpcf['m_PreEmissionOperators'].append(operator)

            header = '<!-- kv3 encoding:text:version{e21c7f3c-8a33-41c5-9977-a76d3a32aa0d} format:vpcf26:version{26288658-411e-4f14-b698-2e1e5d00dec6} -->'

            with open(vpcf_path, 'w') as fp:
                fp.write(dict_to_kv3_text(vpcf, header))

            print("+ Saved", vpcf_localpath.as_posix())

    print("Looks like we are done!")
    generics = list()
    dd = {}
    for n, nn in unt.items():
        #for nn in unt[n]:
        #    print(f'{nn})
        if '_generic' in nn:
            generics.append(str(n))
            continue
        elif nn[0]:#.startswith('m_'):
            try:
                dd[nn[0]].append(n)
            except (KeyError, AttributeError):
                dd[nn[0]] = list()
                dd[nn[0]].append(n)
            continue

        print(f"'{n}': '',  #", nn)

    for k, v in dd.items():
        print('------', k)
        spaces = '            '
        if k.startswith('m_'):
            spaces = '        '
        for i, n in enumerate(v):
            if i == 0: print(f"    '{n}': '',")
            else: print(f"{spaces}'{n}': '',")
        print()

    for n in generics:
        print(f"'{n}': '',")

    for child in children:
        if str(child.as_posix()) not in imports:
            print(child, "was not imported...")
    for fb in fallbacks:
        print(fb)
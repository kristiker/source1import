import shared.datamodel as dmx
if __name__ is None:
    import utils.shared.datamodel as dmx

from pathlib import Path

class resource(str): pass  # kv3 resource

class dynamicparam(str): pass
class maxof(dynamicparam): pass
class minof(dynamicparam): pass

class BoolToSetKV:
    def __init__(self, k, v):
        self.k, self.v = k, v

vpcf_PreOPs = set()

def PreOP(cls: str):
    vpcf_PreOPs.add(cls)
    return cls

#TODO: are arrays different from vectors? vec seems to have no newlines and no comma at end

pcf_to_vpcf = {
    # name/functionName -> class
    'renderers': ( 'm_Renderers',
    {
        'render_animated_sprites':  'C_OP_RenderSprites',
            'animation rate': 'm_flAnimationRate',
            'second sequence animation rate': 'm_flAnimationRate2',
            'Visibility Proxy Radius': '',
            'Visibility Proxy Input Control Point Number': '',
            'Visibility input distance maximum': '',
            'Visibility input distance minimum': '',
            'Visibility Radius Scale maximum': maxof('m_flRadiusScale'),
            'Visibility Alpha Scale maximum': maxof('m_flAlphaScale'),
            'Visibility Alpha Scale minimum': minof('m_flAlphaScale'),
            'Visibility input minimum': 'm_flMinSize',
            'Visibility input maximum': 'm_flMaxSize',
            'Visibility Radius Scale minimum': minof('m_flRadiusScale'),
            'Visibility input dot minimum': 'm_flStartFadeDot',
            'Visibility input dot maximum': 'm_flEndFadeDot',
            'use animation rate as FPS': '',
            'animation_fit_lifetime': BoolToSetKV('m_nAnimationType', 'ANIMATION_TYPE_FIT_LIFETIME'),
            'orientation control point': 'm_nOrientationControlPoint',
            'orientation_type': 'm_nOrientationType',
            'length fade in time': '',
            'min length': 'm_flMinSize',
            'max length': 'm_flMaxSize',
            'constrain radius to length': '',
            'ignore delta time': '',
            'operator time offset max': '',
            'operator strength random scale min': '',
            'operator start fadein': '',
            'operator end fadein': '',
            'operator start fadeout': '',
            'operator end fadeout': '',
            'operator fade oscillate': '',
        'render_rope': 'C_OP_RenderRopes',
            'texel_size': '',
            'texture_scroll_rate': '',
        'render_screen_velocity_rotate': '',
        'render_sprite_trail': 'C_OP_RenderTrails',
             'tail color and alpha scale factor': '',
        'render_blobs': 'C_OP_RenderBlobs',
        'Render models': 'C_OP_RenderModels',
            # m_ModelList =
            # [
            # 	 {
            # 	 	m_model = resource:"asd"
            # 	 },
            # ]
            'sequence 0 model': '',
            'orient model z to normal': '',
        'render_project': 'C_OP_RenderProjected',
    }),

    'operators': ('m_Operators', {
        'Lifespan Decay': 'C_OP_Decay',
            # m_bRopeDecay
        'Radius Scale': 'C_OP_InterpolateRadius',
            'radius_start_scale': 'm_flEndScale',
            'radius_end_scale': 'm_flStartScale',
            'scale_bias': 'm_flBias',
            'end_time': 'm_flEndTime',
            'ease_in_and_out': 'm_bEaseInAndOut',
            'start_time': '',

        'Alpha Fade In Random': 'C_OP_FadeIn',
            'proportional 0/1': 'm_bProportional',
            'fade out time min': 'm_flFadeOutTimeMin', # TODO m_(type)joinedcapitalizedwords.stripnumber/
            'fade out time max': 'm_flFadeOutTimeMax',
            'fade in time min': 'm_flFadeInTimeMin',
            'fade in time max': 'm_flFadeInTimeMax',
            'ease in and out': 'm_bEaseInAndOut',

        'Alpha Fade Out Random': 'C_OP_FadeOut',
            'proportional 0/1': 'm_bProportional',
            'fade out time min': 'm_flFadeOutTimeMin',
            'fade out time max': 'm_flFadeOutTimeMax',
            'ease in and out': 'm_bEaseInAndOut',
            'fade bias': 'm_flFadeBias',

        'Movement Basic': 'C_OP_BasicMovement',
            'gravity': 'm_Gravity',
            'drag': 'm_fDrag',
            'max constraint passes': 'm_nMaxConstraintPasses',
            'operator end fadeout': '',
            'operator start fadeout': '',
            'operator end fadein': '',
            'operator start fadein': '',
            'operator time offset max': '',
            'operator fade oscillate': '',

        'Movement Dampen Relative to Control Point': 'C_OP_DampenToCP',
            # m_nControlPointNumber
            'dampen scale': 'm_flScale',
            'falloff range': 'm_flRange',

        'Alpha Fade and Decay': 'C_OP_FadeAndKill',
            'end_fade_in_time': 'm_flEndFadeInTime',
            'start_alpha': 'm_flStartAlpha',
            'end_alpha': 'm_flEndAlpha',
            'start_fade_out_time': 'm_flStartFadeOutTime',
            'end_fade_out_time': 'm_flEndFadeOutTime',

        'Rotation Basic': 'C_OP_SpinUpdate',
        'Oscillate Scalar': 'C_OP_OscillateScalar',
            'end time max': 'm_flEndTime_max',
            'end time min': 'm_flEndTime_min',
            'oscillation start phase': 'm_flOscAdd',
            'start/end proportional': 'm_bProportionalOp',
        'Oscillate Vector': 'C_OP_OscillateVector',
            'oscillation frequency max': 'm_FrequencyMax',
            'oscillation frequency min': 'm_FrequencyMin',
            'oscillation rate max': 'm_RateMax',
            'oscillation rate min': 'm_RateMin',
            'oscillation field': 'm_nField',
            'oscillation multiplier': 'm_flOscMult',
            'start time max': 'm_flStartTime_max',
            'start time min': 'm_flStartTime_min',
            'operator time strength random scale max': '',

        'Movement Lock to Control Point': 'C_OP_PositionLock',
            # m_flStartTime_exp, m_flEndTime_exp m_flRange, m_flJumpThreshold, m_flPrevPosScale
            'lock rotation': 'm_bLockRot',
            'start_fadeout_min': 'm_flStartTime_min',
            'start_fadeout_max': 'm_flStartTime_max',
            'end_fadeout_min': 'm_flEndTime_min',
            'end_fadeout_max': 'm_flEndTime_max',
            'operator end cap state': 'm_nOpEndCapState',
            'control_point_number': 'm_nControlPointNumber',
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
            'output is scalar of initial random range': '',
            'output is scalar of current value': '',
            'control point': 'm_nControlPoint',
        'Color Fade': 'C_OP_ColorInterpolate',
            'color_fade': 'm_ColorFade',
            'fade_start_time': 'm_flFadeStartTime',
            'fade_end_time': 'm_flFadeEndTime',
        'Rotation Spin Roll': 'C_OP_Spin',
            'spin_rate_degrees': 'm_nSpinRateDegrees',
            'spin_stop_time': 'm_fSpinRateStopTime',
            'operator strength random scale max': '',
            'operator strength random scale min': '',
            'operator strength scale seed': '',
            'spin_rate_min': 'm_nSpinRateMinDegrees',
        'Alpha Fade In Simple': 'C_OP_FadeInSimple',
            'proportional fade in time': 'm_flFadeInTime',
        'Cull when crossing plane': 'C_OP_PlaneCull',
        'Set child control points from particle positions': 'C_OP_SetChildControlPoints',
            '# of control points to set': 'm_nNumControlPoints',
            'First control point to set': 'm_nFirstControlPoint',
            'first particle to copy': dynamicparam('m_nFirstSourcePoint'),
        'Alpha Fade Out Simple': 'C_OP_FadeOutSimple',
            'proportional fade out time': 'm_flFadeOutTime',
        'Ramp Scalar Linear Random': 'C_OP_RampScalarLinear',
            'ramp rate max': 'm_RateMax',
            'ramp field': 'm_nField',
        'Remap Speed to Scalar': 'C_OP_RemapSpeed',
        'Lifespan Minimum Velocity Decay': 'C_OP_VelocityDecay',
            'minimum velocity': 'm_flMinVelocity',
        'Rotation Orient Relative to CP': 'C_OP_Orient2DRelToCP',
        'Movement Lock to Bone': 'C_OP_LockToBone',
            'lifetime fade end': '',
            'lifetime fade start': '',
        'Cull Random': 'C_OP_Cull',
            'Cull Percentage': '',
            'Cull End Time': '',
        'Movement Place On Ground': 'C_OP_MovementPlaceOnGround',
        'Remap Scalar': 'C_OP_RemapScalar',
        'Lifespan Maintain Count Decay': 'C_OP_DecayMaintainCount',
        'Remap Control Point to Vector': 'C_OP_RemapCPtoVector',
        'Color Light from Control Point': 'C_OP_ControlpointLight',
            'Compute Normals From Control Points': 'm_bUseNormal',
            'Clamp Minimum Light Value to Initial Color': 'm_bClampLowerRange',
            'Light 1 0% Distance': 'm_LightZeroDist1',
            'Light 1 50% Distance': 'm_LightFiftyDist1',
            'Light 1 Color': 'm_LightColor1',
            'Light 1 Control Point Offset': 'm_vecCPOffset1',
            'Light 1 Control Point': 'm_nControlPoint1',
            'Initial Color Bias': 'm_flScale',
            'Light 2 Control Point': 'm_nControlPoint2',
            'Light 2 Control Point Offset': 'm_vecCPOffset2',
            'Light 2 Color': 'm_LightColor2',
            'Light 2 50% Distance': 'm_LightFiftyDist2',
            'Light 2 0% Distance': 'm_LightZeroDist2',
            'Light 1 Type 0=Point 1=Spot': 'm_bLightType1',
            'Light 1 Direction': '',
        'Movement Max Velocity': 'C_OP_MaxVelocity',
            'Maximum Velocity': '',
        'Remap Dot Product to Scalar': 'C_OP_RemapDotProductToScalar',
            'first input control point': '',
            'second input control point': '',
            'input minimum (-1 to 1)': '',
        'Remap Distance Between Two Control Points to Scalar': 'C_OP_DistanceBetweenCPs',
        'Remap Control Point to Scalar': 'C_OP_RemapCPtoScalar',
            'input control point number': '',
            'input field 0-2 X/Y/Z': '',
        'Movement Match Particle Velocities': 'C_OP_VelocityMatchingForce',
            'Speed Matching Strength': '',
            'Direction Matching Strength': '',

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
        'Set Control Point to Impact Point': PreOP('C_OP_SetControlPointToImpactPoint'),
            'Trace Update Rate': 'm_flUpdateRate',
            'Trace Direction Override': 'm_vecTraceDir',
            'Control Point to Set': 'm_nCPOut',
        "Set Control Point To Particles' Center": PreOP('C_OP_SetControlPointToCenter'),
            'Control Point Number to Set': '',
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
            'randomly distribute to highest supplied Control Point': '',
            'randomly distribution growth time': 'm_flEndCPGrowthTime',
            'scale cp (distance/speed/local speed)': 'm_nScaleCP',
            'create in model': '',

        'Inherit Velocity': '',
        'Move Particles Between 2 Control Points': 'C_INIT_MoveBetweenPoints',
        '': '',
        '': '',
        '': '',
        '': '',
        '': '',
        'Lifetime Random': 'C_INIT_RandomLifeTime',
            'lifetime_min': 'm_fLifetimeMin',
            'lifetime_max': 'm_fLifetimeMax',
            'lifetime_random_exponent': 'm_fLifetimeRandExponent',

        'Color Random': 'C_INIT_RandomColor',
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
            'randomly_flip_direction': 'm_bRandomlyFlipDirection',
            'rotation_offset_max': 'm_flDegreesMax',
            'rotation_offset_min': 'm_flDegreesMin',
            'rotation_initial': 'm_flDegrees',

        'Alpha Random': 'C_INIT_RandomAlpha',
            'alpha_max': 'm_nAlphaMin',
            'alpha_min': 'm_nAlphaMax',
            'alpha_random_exponent': 'm_flAlphaRandExponent',
            'operator time offset max': '',
            'operator strength random scale min': '',

        'Position Modify Offset Random': 'C_INIT_PositionOffset',
            'offset max': 'm_OffsetMin',
            'offset min': 'm_OffsetMax',
            'offset in local space 0/1': 'm_bLocalCoords',
            'offset proportional to radius 0/1': 'm_bProportional',

        'Sequence Random': 'C_INIT_RandomSequence',
            'sequence_max': 'm_nSequenceMax',
            'sequence_min': 'm_nSequenceMin',
            'shuffle': 'm_bShuffle',
            'linear': 'm_bLinear',

        'Sequence Two Random': 'C_INIT_RandomSecondSequence',
        'Radius Random': 'C_INIT_RandomRadius',
            'radius_min': 'm_flRadiusMin',
            'radius_max': 'm_flRadiusMax',
            'radius_random_exponent': 'm_flRadiusRandExponent',

        'Rotation Speed Random': 'C_INIT_RandomRotationSpeed',
            'rotation_speed_random_min': 'm_flDegreesMin',
            'rotation_speed_random_max': 'm_flDegreesMax',
            'rotation_speed_constant': '',

        'Position Within Box Random': 'C_INIT_CreateWithinBox',
            'max': 'm_vecMax',
            'min': 'm_vecMin',
            'use local space': 'm_bLocalSpace',

        'Rotation Yaw Flip Random': 'C_INIT_RandomYawFlip',
            'Flip Percentage': 'm_flPercent',

        'remap initial scalar': 'C_INIT_RemapScalar',
            'input minimum': 'm_flInputMin',
            'input maximum': 'm_flInputMax',
            'output minimum': 'm_flOutputMin',
            'output maximum': 'm_flOutputMax',
            'output is scalar of initial random range': BoolToSetKV('m_nSetMethod', 'PARTICLE_SET_SCALE_INITIAL_VALUE'), # unsure
            'output field': 'm_nFieldOutput',

        'Position Modify Warp Random': 'C_INIT_PositionWarp',
            'warp min': 'm_vecWarpMin',
            'warp max': 'm_vecWarpMax',
            'warp transition time (treats min/max as start/end sizes)': 'm_flWarpTime',
            'warp transition start time': 'm_flWarpStartTime',

        'Velocity Noise': 'C_INIT_InitialVelocityNoise',
            'Time Noise Coordinate Scale': dynamicparam('m_flNoiseScale'),
            'Spatial Noise Coordinate Scale': dynamicparam('m_flNoiseScaleLoc'),
            'Absolute Value': 'm_vecAbsVal',
            'Apply Velocity in Local Space (0/1)': 'm_bLocalSpace',
            'Invert Abs Value': 'm_vecAbsValInv',
            'Spatial Coordinate Offset': dynamicparam('m_vecOffsetLoc'),
            'Time Coordinate Offset': dynamicparam('m_flOffset'),
            'Control Point Number': 'm_nControlPointNumber',

        'Trail Length Random': 'C_INIT_RandomTrailLength',
            'length_min': 'm_flMinLength',
            'length_max': 'm_flMaxLength',

        'Lifetime From Sequence': 'C_INIT_SequenceLifeTime',
            'Frames Per Second': 'm_flFramerate',
            'operator strength random scale max': '',
            'operator strength scale seed': '',

        'Remap Initial Scalar': 'C_INIT_RemapScalar', # 'remap initial scalar' duplicate wtf
            'emitter lifetime end time (seconds)': 'm_flStartTime',
            'emitter lifetime start time (seconds)': 'm_flEndTime',

        'Remap Initial Distance to Control Point to Scalar': '',
            #'distance minimum': 'm_flInputMin'
            'distance maximum': 'm_flInputMax',
        'Position Along Ring': 'C_INIT_RingWave',
            'initial radius': 'm_flInitialRadius',
            'thickness': 'm_flThickness',
            'min initial speed': 'm_flInitialSpeedMin',
            'max initial speed': 'm_flInitialSpeedMax',
            'even distribution': 'm_bEvenDistribution',
            'XY velocity only': 'm_bXYVelocityOnly',
            'even distribution count': 'm_flParticlesPerOrbit',
            'control point number': 'm_nControlPointNumber',
            'Override CP (X/Y/Z *= Radius/Thickness/Speed)': 'm_nOverrideCP',
            # m_flRoll m_flPitch m_flYaw m_nOverrideCP2
        'Velocity Random': 'C_INIT_VelocityRandom',
            'random_speed_max': dynamicparam('m_fSpeedMax'),
            'random_speed_min': dynamicparam('m_fSpeedMin'),
            # this one has got 'speed_in_local_coordinate_system_min', etc from C_INIT_CreateWithinSphere random
            # but on this one its a dynamicparam, so can you skip dynamic paraming on this (and most that dont use random) #TODO
        'Position From Parent Particles': 'C_INIT_CreateFromParentParticles',
            'operator end cap state': 'm_nOpEndCapState',
            'Inherited Velocity Scale': 'm_flVelocityScale',
            'Random Parent Particle Distribution': 'm_bRandomDistribution',
            # m_flIncrement = 11.0 m_bRandomDistribution = true m_nRandomSeed = 1 m_bSubFrame = false
        'Remap Scalar to Vector': 'C_INIT_RemapScalarToVector',
            'use local system': '',
            # m_flVelocityScale = 1.0
            # m_flIncrement = 11.0
            # m_bRandomDistribution = true
            # m_nRandomSeed = 1
            # m_bSubFrame = false
        'lifetime from sequence': 'C_INIT_SequenceLifeTime',
        'Scalar Random': 'C_INIT_RandomScalar',
            # this likely has m_flMin & clashes with m_vecMin TODO FIXME
        'Remap Control Point to Scalar': 'C_INIT_RemapCPtoScalar',
        'Position on Model Random': 'C_INIT_CreateOnModel',
            'force to be inside model': '',
            'direction bias': '',
        'Velocity Set from Control Point': 'C_INIT_VelocityFromCP',
        'Position Modify Place On Ground': 'C_INIT_PositionPlaceOnGround',
            'collision group': '',
            'max trace length': '',
            'kill on no collision': '',
            'offset': '',
            'set normal': '',
            'include water': '',
        'Velocity Inherit from Control Point': 'C_INIT_InheritVelocity',
            'velocity scale': '',
        'Remap Noise to Scalar': 'C_INIT_CreationNoise',
            'time noise coordinate scale': '',
            'spatial noise coordinate scale': '',
            'world time noise coordinate scale': '',
        'Lifetime Pre-Age Noise': 'C_INIT_AgeNoise',
            'start age minimum': 'm_flAgeMin',
            'start age maximum': 'm_flAgeMax',
        'Position In CP Hierarchy': '',
        'Lifetime from Time to Impact': 'C_INIT_LifespanFromVelocity',
            'maximum trace length': 'm_flMaxTraceLength',
            'trace collision group': 'm_CollisionGroupName',
            'trace offset': 'm_flTraceOffset',
            'trace recycle tolerance': 'm_flTraceTolerance',
            'maximum points to cache': 'm_nMaxPlanes',
            'bias distance': 'm_vecComponentScale',
            # m_bIncludeWater = false
        'Position from Parent Cache': 'C_INIT_CreateFromPlaneCache',
        'Rotation Yaw Random': 'C_INIT_RandomYaw',
            'yaw_offset_max': '',
            'yaw_offset_min': '',
        'Position Along Path Sequential': 'C_INIT_CreateSequentialPathV2',
            'particles to map from start to end': '',
            'end control point number': '',
            'maximum distance': '',
            'start control point number': '',
        'Velocity Repulse from World': 'C_INIT_InitialRepulsionVelocity',
            'Trace Length': '',
            'Inherit from Parent': '',
            'maximum velocity': '',
            'control points to broadcast to children (n + 1)': '',
        'Cull relative to Ray Trace Environment': 'C_INIT_RtEnvCull',
            'cull on miss': '',
            'cull normal': '',
            'ray trace environment name': '',
            'velocity test adjust lifespan': '',
            'use velocity for test direction': '',
        'Color Lit Per Particle': 'C_INIT_ColorLitPerParticle',
            'light bias': 'm_flTintPerc',
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
            'operator time offset max': '',
            'operator strength random scale min': '',
            'operator end cap state': 'm_nOpEndCapState',

        }),
        'emit_continuously': ('C_OP_ContinuousEmitter', {
            'emission_duration': dynamicparam('m_flEmissionDuration'),
            'emission_rate': dynamicparam('m_flEmitRate'),
            'emission_start_time': dynamicparam('m_flStartTime'),
            'emission count scale control point': 'm_nScaleControlPoint',
            'emission count scale control point field': 'm_nScaleControlPointField',
            'operator end fadein': '',
            'scale emission to used control points': 'm_flScalePerParentParticle', # not sure
            'operator end fadeout': '',
            'operator start fadein': '',
            'operator start fadeout': '',
            'use parent particles for emission scaling': '',
            'operator fade oscillate': '',
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
            'operator strength random scale max': '',
            'operator strength random scale min': '',
            'operator strength scale seed': '',
            'object local space axis 0/1': 'm_bLocalSpace',
        }),
        'random force': ('C_OP_RandomForce', {
            'min force': 'm_MinForce',
            'max force': 'm_MaxForce',
            'operator fade oscillate': '',
            'operator end fadeout': '',
            'operator start fadeout': '',
            'operator end fadein': '',
            'operator start fadein': '',
            'operator time scale min': '',
            'operator time scale max': '',
            'operator strength random scale max': '',
            'operator strength scale seed': '',
        }),
        'Force based on distance from plane': ('C_OP_ForceBasedOnDistanceToPlane', {
            'Max Distance from plane': 'm_flMaxDist',
            'Force at Max distance': 'm_vecForceAtMaxDist',
            'Exponent': 'm_flExponent',
            '': 'm_vecPlaneNormal',
            '': 'm_nControlPointNumber',
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
            'operator start fadeout': '',
            'operator end fadeout': '',
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
   }),

    'constraints': ('m_Constraints', {
        'Constrain distance to control point': ('C_OP_ConstrainDistance', {
            'minumum distance': 'm_fMinDistance',
            'maximum distance': 'm_fMaxDistance',
            'offset of center': 'm_CenterOffset',
            '': 'm_nControlPointNumber',
            '': 'm_nScaleCP',
            'global center point': 'm_bGlobalCenter',
        }),
        'Prevent passing through a plane': ('C_OP_PlanarConstraint', {
            'plane point': 'm_PointOnPlane',
            'plane normal': 'm_PlaneNormal',
            'maximum sim tick rate': '',
            'minimum sim tick rate': '',
            'rotation_speed': '',
            'cull_radius': dynamicparam('m_flRadiusScale'), # unsure
            'draw through leafsystem': '',
            'control point number': 'm_nControlPointNumber',
            'control point to disable rendering if it is the camera': '',
            'control point to only enable rendering if it is the camera': '',
            'sequence_number 1': '',
            'minimum free particles to aggregate': '',
            'bounding_box_control_point': '',
            'rotation': '',
            'sequence_number': '',
            'group id': '',
            'cull_cost': '',
            'minimum CPU level': '',
            'minimum GPU level': '',
        }),
        'Collision via traces': ('C_OP_WorldTraceConstraint', {
            'trace accuracy tolerance': 'm_flTraceTolerance',
            'collision group': 'm_CollisionGroupName', # s2defval = 'NONE'
            'amount of slide': dynamicparam('m_flSlideAmount'),
            'amount of bounce': dynamicparam('m_flBounceAmount'),
            'collision mode': 'm_nCollisionMode',
            'radius scale': 'm_flRadiusScale',
            'brush only': 'm_bBrushOnly',
            'Confirm Collision': 'm_flCollisionConfirmationSpeed',
            'control point movement distance tolerance': 'm_flCpMovementTolerance',
            'minimum speed to kill on collision': 'm_flMinSpeed',
            'kill particle on collision': 'm_bKillonContact',
            'operator end fadein': '',
            'operator start fadein': '',
        }),
    }),

    'children': 'm_Children',
    'material': ('m_Renderers', 'm_hTexture', 'm_hMaterial'), # TODO FIXME

    # bare replacement
    'batch particle systems': '',
    'aggregation radius': '',
    'view model effect': '',
    'screen space effect': '',
    'maximum time step': '',
    'minimum rendered frames': '',
    'minimum simulation time step': '',
    'freeze simulation after time': '',
    'preventNameBasedLookup': '',
    'maximum sim tick rate': '',
    'minimum sim tick rate': '',
    'rotation_speed': '',
    'cull_radius': '',
    'draw through leafsystem': '',
    'control point to disable rendering if it is the camera': '',
    'control point to only enable rendering if it is the camera': '',
    'sequence_number 1': '',
    'minimum free particles to aggregate': '',
    'bounding_box_control_point': '',
    'rotation': '',
    'sequence_number': '',
    'group id': '',
    'cull_cost': '',
    'minimum CPU level': '',
    'minimum GPU level': '',
    'max_particles':                    'm_nMaxParticles',
    'initial_particles':                'm_nInitialParticles',
    'cull_replacement_definition':      '',
    'fallback replacement definition':  'm_hFallback', # not a string on pcf, its value is an id
    'fallback max count':               'm_nFallbackMaxCount',
    'radius':                           'm_flConstantRadius',
    'color':                            'm_ConstantColor',
    'maximum draw distance':            'm_flMaxDrawDistance',
    'time to sleep when not drawn':     'm_flNoDrawTimeToGoToSleep',
    'Sort particles':                   'm_bShouldSort',
    'bounding_box_min':                 'm_BoundingBoxMin',
    'bounding_box_max':                 'm_BoundingBoxMax',

    '_pcf_operator_globals': {
        'operator start fadein': '',
        'operator end fadein': '',
        'operator start fadeout': '',
        'operator end fadeout': '',

    },

}

explosions_fx = Path(r'D:\Users\kristi\Documents\GitHub\source1import\utils\shared\particles\explosions_fx.pcf')
lightning = Path(r'D:\Users\kristi\Documents\GitHub\source1import\utils\shared\particles\lighting.pcf')

particles_in = Path(r'D:\Games\steamapps\common\Half-Life Alyx\content\csgo\particles')
particles_out = Path(r'D:\Games\steamapps\common\Half-Life Alyx\content\hlvr_addons\csgo\particles')
#particles_out = Path(r'C:\Users\kristi\Desktop\Source 2\content\hlvr_addons\addon\particles')
def is_valid_pcf(x: dmx.DataModel):
    return ('particleSystemDefinitions' in x.elements[0].keys() and
            x.elements[1].type == 'DmeParticleSystemDefinition'
        )

def guess_key_name(key, value):
    key_words = key.replace('_', ' ').split(' ')

    shorts = {'minimum':'min', 'maximum':'max', 'simulation': 'sim', 'rotation': 'rot'}
    typepreffix = {
        bool:'b', float:'fl', int:'n', resource:'h'
    }

    guess = 'm_' + typepreffix.get(type(value), '')
    # TODO: list -> vec, ang, ''
    for kw in key_words:
        if kw.startswith('('):
            break
        kw = shorts.get(kw, kw)
        guess += kw.capitalize()
    return guess

def tests():
    print(x.elements[0].keys())
    print(x.elements[1].type)
materials = []
children = []
fallbacks = []
def pcfkv_convert(key, value):

    if not (vpcf_translation:= pcf_to_vpcf.get(key)):
        if vpcf_translation is None:
            un(key, '_generic')
        return guess_key_name(key, value), value

    if key == "material":
        materials.append(value)
    outKey, outVal = key, value

    if isinstance(vpcf_translation, str):  # simple translation
        if value == []:
            return
        if isinstance(value, dmx._ElementArray):
            if key == 'children':
                outVal = []
                for child in value:
                    if not child.type == 'DmeParticleChild': # TODO dont need
                        continue
                    children.append(child['child'].name)
                    child_resrc_ref = resource(child['child'].name) # TODO: proper resource path
                    outVal.append(dict(m_ChildRef = child_resrc_ref))
                return vpcf_translation, outVal

            else:
                print('Warning:', key, "is an unhandled element_array")
                return

        if vpcf_translation == 'm_hFallback':
            if not value:
                return
            return vpcf_translation, resource(value)

        return vpcf_translation, value
    elif isinstance(vpcf_translation, tuple):
        if isinstance(vpcf_translation[1], str):  # insert to another dict
            return
        elif not isinstance(vpcf_translation[1], dict):
            return

        if not isinstance(value, list):
            print(key, "is not a list?", value)
            return

        outKey = vpcf_translation[0]
        outVal = []

        for opitem in value:
            bWasTuple = False
            sub_translation = vpcf_translation[1]
            if not (className := sub_translation.get(opitem.name)):
                if className is None:
                    if opitem.name == 'emit_continuously':
                        print("WHAT", sub_translation)
                    un(opitem.name, outKey)
                continue
            if isinstance(className, tuple):
                className, sub_translation = className
                bWasTuple = True
            subKV = { '_class': className }

            for key2, value2 in opitem.items():
                if key2 == 'functionName':
                    if value2 != opitem.name:
                        print("functionName mismatch", key2, opitem.name)
                    continue

                if subkey:=sub_translation.get(key2):
                    if isinstance(subkey, BoolToSetKV):
                        if not value2:
                            continue
                        subkey, value = subkey.k, subkey.v
                    elif isinstance(subkey, minof):
                        if str(subkey) in subKV:
                            if not isinstance(subKV[subkey], dict): # not a dynamicparam
                                subKV[subkey] = dict(
                                    m_nType = "PF_TYPE_RANDOM_UNIFORM",
                                    m_flRandomMin = value2,
                                    m_flRandomMax = subKV[subkey]
                                )
                            else:
                                subKV[subkey]['m_flRandomMin'] = value2
                            continue

                        else: value = dict(
                                    m_nType = "PF_TYPE_RANDOM_UNIFORM",
                                    m_flRandomMin = value2,
                                )

                    elif isinstance(subkey, maxof):
                        ...
                    elif isinstance(subkey, dynamicparam):
                        value2 = {'m_nType': "PF_TYPE_LITERAL",'m_flLiteralValue': value2}
                    #elif bWasTuple:

                    ## no maxof for num_to_emit workaround
                    #if subkey in subKV and isinstance(subKV[subkey], dict):
                    #    # TODO if min add max if max add min
                    #    subKV[subkey]['m_flRandomMax'] = value
                    subKV[subkey] = value2
                elif subkey is None:
                    un(key2, opitem.name)
                    #guess_key_name not here, change logic TODO

            outVal.append(subKV)

    return outKey, outVal

def dict_to_kv3_text(
        kv3dict: dict,
        header = '<!-- kv3 encoding:text:version{e21c7f3c-8a33-41c5-9977-a76d3a32aa0d} format:generic:version{7412167c-06e9-4698-aff2-e63eb59037e7} -->'
    ):
    kv3 = header + '\n'

    def obj_serialize(obj, indent = 1, dictKey = False):
        preind = ('\t' * (indent-1))
        ind = ('\t' * indent)
        if obj is None:
            return 'null'
        elif isinstance(obj, resource):
            #print(obj, "Is resource:", pcf_path.stem, f'resource:"particles/{pcf_path.stem}/{obj}.vpcf"')
            return f'resource:"particles/{pcf_path.stem}/{obj}.vpcf"'
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
    for pcf_path in particles_in.glob('*.pcf'):
        #print(f"Reading particles/{pcf_path.name}")
        x = dmx.load(pcf_path)
        if not is_valid_pcf(x):
            print("Invalid!!")
            #tests()
            continue

        root = (particles_out / pcf_path.stem)
        root.mkdir(exist_ok=True)
        for datamodel in x.find_elements(elemtype='DmeParticleSystemDefinition'):
            imports.append(datamodel.name)
            vpcf = dict(_class = "CParticleSystemDefinition")
            for key, value in datamodel.items():
                if converted_kv:= pcfkv_convert(key, value):
                    vpcf[converted_kv[0]] = converted_kv[1]

            for operator in vpcf.get('m_Operators', ()):
                if not operator.get('_class') in vpcf_PreOPs:
                    continue
                vpcf['m_Operators'].remove(operator)
                vpcf.setdefault('m_PreEmissionOperators', list())
                vpcf['m_PreEmissionOperators'].append(operator)

            header = '<!-- kv3 encoding:text:version{e21c7f3c-8a33-41c5-9977-a76d3a32aa0d} format:vpcf26:version{26288658-411e-4f14-b698-2e1e5d00dec6} -->'
            #print(dict_to_kv3_text(vpcf, header))

            out_particle_path = root / (datamodel.name + '.vpcf')
            with open(out_particle_path, 'w') as fp:
                fp.write(dict_to_kv3_text(vpcf, header))

            print("+ Saved", out_particle_path.relative_to(out_particle_path.parents[2]).as_posix())
            #break

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
        for n in v:
            print(f"{spaces}'{n}': '',")
        print()

    for n in generics:
        print(f"'{n}': '',")

    for child in children:
        if child not in imports:
            print(child, "was not imported...")
    for fb in fallbacks:
        print(fb)

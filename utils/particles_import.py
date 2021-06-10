from dataclasses import dataclass
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

__all__ = ('ImportPCFtoVPCF', 'ImportParticleSnapshotFile')

BEHAVIOR_VERSION = 8

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
    def __repr__(self):
        return f"{self.__class__.__name__}('{self.mother}', '{self.name}')"

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

@dataclass(frozen=True)
class BoolToSetKV:
    k: str
    v: str
    def __call__(self, oldval):
        if oldval: return self.k, self.v

@dataclass(frozen=True)
class Discontinued:
    "This parameter worked on particle systems with behaviour versions lower than `self.at"
    t: str = ''
    at: int = -1
    def __bool__(self): return False # FIXME

Deprecated = {
    9: ('m_bUseHighestEndCP')
}

class Multiple:
    def __init__(self, *args, **kwargs):
        self.bare_replacements = args
        self.kw_replacements = kwargs

@dataclass(frozen=True)
class SingleColour:
    "Single component for a key of type: vec4"
    default = [255, 255, 255, 255]
    t: str
    place:int
    def __call__(self, oldval, existing = default):
        rv = existing
        rv[self.place] = oldval
        return self.t, rv

vpcf_PreEmisionOperators = (
    'C_OP_RemapSpeedtoCP',
    'C_OP_SetControlPointPositions',
    'C_OP_SetControlPointToPlayer',
    'C_OP_SetControlPointToCenter',
    'C_OP_SetControlPointRotation',
    'C_OP_SetControlPointToImpactPoint',
)

pcf_to_vpcf = {
    # name/functionName -> class
    'renderers': ( 'm_Renderers', {
        'render_points': 'C_OP_RenderPoints',
        'render_animated_sprites':  'C_OP_RenderSprites',
            'animation rate': 'm_flAnimationRate',
            'second sequence animation rate': 'm_flAnimationRate2',
            'cull system when CP normal faces away from camera': Discontinued(),
            'cull system starting at this recursion depth': Discontinued(),
            'use animation rate as FPS': 'm_bAnimateInFPS',
            'animation_fit_lifetime': BoolToSetKV('m_nAnimationType', 'ANIMATION_TYPE_FIT_LIFETIME'), # parser gives 'm_bFitCycleToLifetime',
            'orientation control point': 'm_nOrientationControlPoint',
            'orientation_type': 'm_nOrientationType',
            'length fade in time': Discontinued(),
            'min length': 'm_flMinSize',
            'max length': 'm_flMaxSize',
            'constrain radius to length': Discontinued(),
            'ignore delta time': Discontinued(),
            'sheet': Discontinued(), # probably some obscure m_hTexture ?
            'Visibility Camera Depth Bias': 'm_flDepthBias',

        'render_rope': 'C_OP_RenderRopes',
            'texel_size': '',#radius scale?#Multiple('m_flFinalTextureScaleU', 'm_flFinalTextureScaleV'), # unsure
            'texture_scroll_rate': dynamicparam('m_flTextureVScrollRate'),
            'subdivision_count': 'm_flTessScale',
            'scale offset by CP distance': 'm_flScaleVOffsetByControlPointDistance',
            'scale scroll by CP distance': 'm_flScaleVScrollByControlPointDistance',
        'render_screen_velocity_rotate': NotImplemented,
            'forward_angle': 'm_flForwardDegrees',
            'rotate_rate(dps)': 'm_flRotateRateDegrees',
        'render_sprite_trail': ('C_OP_RenderTrails', {
            'animation rate': 'm_flAnimationRate',
            'length fade in time': 'm_flLengthFadeInTime',
            'max length': 'm_flMaxLength',
            'min length': 'm_flMinLength',
            'constrain radius to length': 'm_bConstrainRadius',
            'ignore delta time': 'm_bIgnoreDT',
            'tail color and alpha scale factor': Multiple(
                m_vecTailColorScale = lambda v: v[:3],
                m_flTailAlphaScale = lambda v: v[3]
            ),
            'cull system when CP normal faces away from camera': Discontinued(),
            'cull system starting at this recursion depth': Discontinued(),
            'Visibility Camera Depth Bias': 'm_flDepthBias', # weird name source engine but ok
        }),
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
            'scale animation rate': 'm_bScaleAnimationRate',
            'skin number': 'm_nSkin',
        'render_project': 'C_OP_RenderProjected',
        'Render projected': 'C_OP_RenderProjected',
    }),

    'operators': ('m_Operators', {
        'Movement Basic': ('C_OP_BasicMovement', {
            'gravity': 'm_Gravity',
            'drag': 'm_fDrag',
            'max constraint passes': 'm_nMaxConstraintPasses',
        }),
        'Alpha Fade and Decay': ('C_OP_FadeAndKill', {        
            'start_alpha': 'm_flStartAlpha',
            'end_alpha': 'm_flEndAlpha',
            'start_fade_in_time': 'm_flStartFadeInTime',      
            'end_fade_in_time': 'm_flEndFadeInTime',
            'start_fade_out_time': 'm_flStartFadeOutTime',
            'end_fade_out_time': 'm_flEndFadeOutTime',
        }),
        'Alpha Fade and Decay for Tracers': ('C_OP_FadeAndKillForTracers', {
            'start_alpha': 'm_flStartAlpha',
            'end_alpha': 'm_flEndAlpha',
            'start_fade_in_time': 'm_flStartFadeInTime',
            'end_fade_in_time': 'm_flEndFadeInTime',
            'start_fade_out_time': 'm_flStartFadeOutTime',
            'end_fade_out_time': 'm_flEndFadeOutTime',
        }),
        'Alpha Fade In Random': ('C_OP_FadeIn', {
            'fade in time min': 'm_flFadeInTimeMin',
            'fade in time max': 'm_flFadeInTimeMax',
            'fade in time exponent': 'm_flFadeInTimeExp',
            'proportional 0/1': 'm_bProportional',
        }),
        'Alpha Fade Out Random': ('C_OP_FadeOut', {
            'fade out time min': 'm_flFadeOutTimeMin',
            'fade out time max': 'm_flFadeOutTimeMax',
            'fade out time exponent': 'm_flFadeOutTimeExp',
            'proportional 0/1': 'm_bProportional',
            'ease in and out': 'm_bEaseInAndOut',
            'fade bias': 'm_flFadeBias',
        }),
        'Alpha Fade In Simple': ('C_OP_FadeInSimple', {
            'proportional fade in time': 'm_flFadeInTime',
        }),
        'Alpha Fade Out Simple': ('C_OP_FadeOutSimple', {
            'proportional fade out time': 'm_flFadeOutTime',
        }),
        'Clamp Scalar': ('C_OP_ClampScalar', {
            'output field': 'm_nFieldOutput',
            'output minimum': 'm_flOutputMin',
            'output maximum': 'm_flOutputMax',
        }),
        'Clamp Vector': ('C_OP_ClampVector', {
            'output field': 'm_nFieldOutput',
            'output minimum': 'm_vecOutputMin',
            'output maximum': 'm_vecOutputMax',
        }),
        'Oscillate Scalar': ('C_OP_OscillateScalar', {
            'oscillation field': 'm_nField',
            'oscillation rate min': 'm_RateMin',
            'oscillation rate max': 'm_RateMax',
            'oscillation frequency min': 'm_FrequencyMin',
            'oscillation frequency max': 'm_FrequencyMax',
            'proportional 0/1': 'm_bProportional',
            'start time min': 'm_flStartTime_min',
            'start time max': 'm_flStartTime_max',
            'end time min': 'm_flEndTime_min',
            'end time max': 'm_flEndTime_max',
            'start/end proportional': 'm_bProportionalOp',
            'oscillation multiplier': 'm_flOscMult',
            'oscillation start phase': 'm_flOscAdd',
        }),
        'Oscillate Scalar Simple': ('C_OP_OscillateScalarSimple', {
            'oscillation field': 'm_nField',
            'oscillation rate': 'm_Rate',
            'oscillation frequency': 'm_Frequency',
            'oscillation multiplier': 'm_flOscMult',
            'oscillation start phase': 'm_flOscAdd',
        }),
        'Oscillate Vector': ('C_OP_OscillateVector', {
            'oscillation field': 'm_nField',
            'oscillation rate min': 'm_RateMin',
            'oscillation rate max': 'm_RateMax',
            'oscillation frequency min': 'm_FrequencyMin',
            'oscillation frequency max': 'm_FrequencyMax',
            'proportional 0/1': 'm_bProportional',
            'start time min': 'm_flStartTime_min',
            'start time max': 'm_flStartTime_max',
            'end time min': 'm_flEndTime_min',
            'end time max': 'm_flEndTime_max',
            'start/end proportional': 'm_bProportionalOp',
            'oscillation multiplier': 'm_flOscMult',
            'oscillation start phase': 'm_flOscAdd',
        }),
        'Oscillate Vector Simple': ('C_OP_OscillateVectorSimple', {
            'oscillation field': 'm_nField',
            'oscillation rate': 'm_Rate',
            'oscillation frequency': 'm_Frequency',
            'oscillation multiplier': 'm_flOscMult',
            'oscillation start phase': 'm_flOscAdd',
        }),
        'Remap Difference of Sequential Particle Vector to Scalar': ('C_OP_DifferencePreviousParticle', {
            'difference minimum': 'm_flInputMin',
            'difference maximum': 'm_flInputMax',
            'input field': 'm_nFieldInput',
            'output field': 'm_nFieldOutput',
            'output minimum': 'm_flOutputMin',
            'output maximum': 'm_flOutputMax',
            'output is scalar of initial random range': BoolToSetKV('m_nSetMethod', "PARTICLE_SET_SCALE_CURRENT_VALUE"),#'m_bScaleInitialRange',
            'only active within specified difference': 'm_bActiveRange',
            'also set ouput to previous particle': 'm_bSetPreviousParticle',
        }),
        'Remap Scalar': ('C_OP_RemapScalar', {
            'input field': 'm_nFieldInput',
            'input minimum': 'm_flInputMin',
            'input maximum': 'm_flInputMax',
            'output field': 'm_nFieldOutput',
            'output minimum': 'm_flOutputMin',
            'output maximum': 'm_flOutputMax',
        }),
        'Lerp Initial Scalar': ('C_OP_LerpScalar', {
            'start time': 'm_flStartTime',
            'end time': 'm_flEndTime',
            'output field': 'm_nFieldOutput',
            'value to lerp to': 'm_flOutput',
        }),
        'Lerp EndCap Scalar': ('C_OP_LerpEndCapScalar', {
            'lerp time': 'm_flLerpTime',
            'output field': 'm_nFieldOutput',
            'value to lerp to': 'm_flOutput',
        }),
        'Lerp EndCap Vector': ('C_OP_LerpEndCapVector', {
            'lerp time': 'm_flLerpTime',
            'output field': 'm_nFieldOutput',
            'value to lerp to': 'm_vecOutput',
        }),
        'Lerp Initial Vector': ('C_OP_LerpVector', {
            'start time': 'm_flStartTime',
            'end time': 'm_flEndTime',
            'output field': 'm_nFieldOutput',
            'value to lerp to': 'm_vecOutput',
        }),
        'Remap Speed to Scalar': ('C_OP_RemapSpeed', {
            'input minimum': 'm_flInputMin',
            'input maximum': 'm_flInputMax',
            'output field': 'm_nFieldOutput',
            'output minimum': 'm_flOutputMin',
            'output maximum': 'm_flOutputMax',
            'output is scalar of initial random range': BoolToSetKV('m_nSetMethod', "PARTICLE_SET_SCALE_CURRENT_VALUE"),#'m_bScaleInitialRange',
            'output is scalar of current value': BoolToSetKV('m_nSetMethod', "PARTICLE_SET_SCALE_INITIAL_VALUE"),#'m_bScaleCurrent',
        }),
        'Remap CP Speed to CP': ('C_OP_RemapSpeedtoCP', {
            'input control point': 'm_nInControlPointNumber',
            'input minimum': 'm_flInputMin',
            'input maximum': 'm_flInputMax',
            'output control point': 'm_nOutControlPointNumber',
            'Output field 0-2 X/Y/Z': 'm_nField',
            'output minimum': 'm_flOutputMin',
            'output maximum': 'm_flOutputMax',
        }),
        'Remap Model Volume to CP': ('C_OP_RemapModelVolumetoCP', {
            'input control point': 'm_nInControlPointNumber',
            'input volume minimum in cubic units': 'm_flInputMin',
            'input volume maximum in cubic units': 'm_flInputMax',
            'output control point': 'm_nOutControlPointNumber',
            'output minimum': 'm_flOutputMin',
            'output maximum': 'm_flOutputMax',
        }),
        'Remap Particle BBox Volume to CP': ('C_OP_RemapBoundingVolumetoCP', {
            'input volume minimum in cubic units': 'm_flInputMin',
            'input volume maximum in cubic units': 'm_flInputMax',
            'output control point': 'm_nOutControlPointNumber',
            'output minimum': 'm_flOutputMin',
            'output maximum': 'm_flOutputMax',
        }),
        'Remap Average Scalar Value to CP': ('C_OP_RemapAverageScalarValuetoCP', {
            'Scalar field': 'm_nField',
            'input volume minimum': 'm_flInputMin',
            'input volume maximum': 'm_flInputMax',
            'output control point': 'm_nOutControlPointNumber',
            'output minimum': 'm_flOutputMin',
            'output maximum': 'm_flOutputMax',
        }),
        'Ramp Scalar Linear Random': ('C_OP_RampScalarLinear', {
            'ramp field': 'm_nField',
            'ramp rate min': 'm_RateMin',
            'ramp rate max': 'm_RateMax',
            'start time min': 'm_flStartTime_min',
            'start time max': 'm_flStartTime_max',
            'end time min': 'm_flEndTime_min',
            'end time max': 'm_flEndTime_max',
            'start/end proportional': 'm_bProportionalOp',
        }),
        'Ramp Scalar Spline Random': ('C_OP_RampScalarSpline', {
            'ramp field': 'm_nField',
            'ramp rate min': 'm_RateMin',
            'ramp rate max': 'm_RateMax',
            'start time min': 'm_flStartTime_min',
            'start time max': 'm_flStartTime_max',
            'end time min': 'm_flEndTime_min',
            'end time max': 'm_flEndTime_max',
            'start/end proportional': 'm_bProportionalOp',
            'ease out': 'm_bEaseOut',
            'bias': 'm_flBias',
        }),
        'Ramp Scalar Linear Simple': ('C_OP_RampScalarLinearSimple', {
            'ramp field': 'm_nField',
            'ramp rate': 'm_Rate',
            'start time': 'm_flStartTime',
            'end time': 'm_flEndTime',
        }),
        'Ramp Scalar Spline Simple': ('C_OP_RampScalarSplineSimple', {
            'ramp field': 'm_nField',
            'ramp rate': 'm_Rate',
            'start time': 'm_flStartTime',
            'end time': 'm_flEndTime',
            'ease out': 'm_bEaseOut',
        }),
        'Noise Scalar': ('C_OP_Noise', {
            'noise coordinate scale': 'm_fl4NoiseScale',
            'output field': 'm_nFieldOutput',
            'output minimum': 'm_flOutputMin',
            'output maximum': 'm_flOutputMax',
            'additive': 'm_bAdditive',
        }),
        'Noise Vector': ('C_OP_VectorNoise', {
            'noise coordinate scale': 'm_fl4NoiseScale',
            'output field': 'm_nFieldOutput',
            'output minimum': 'm_vecOutputMin',
            'output maximum': 'm_vecOutputMax',
            'additive': 'm_bAdditive',
        }),
        'Lifespan Decay': ('C_OP_Decay', {
        }),
        'Lifespan Minimum Velocity Decay': ('C_OP_VelocityDecay', {
            'minimum velocity': 'm_flMinVelocity',
        }),
        'Lifespan Minimum Alpha Decay': ('C_OP_AlphaDecay', {
            'minimum alpha': 'm_flMinAlpha',
        }),
        'Lifespan Minimum Radius Decay': ('C_OP_RadiusDecay', {
            'minimum radius': 'm_flMinRadius',
        }),
        'Lifespan Maintain Count Decay': ('C_OP_DecayMaintainCount', {
            'count to maintain': 'm_nParticlesToMaintain',
            'decay delay': 'm_flDecayDelay',
            'maintain count scale control point': 'm_nScaleControlPoint',
            'maintain count scale control point field': 'm_nScaleControlPointField',
        }),
        'Cull Random': ('C_OP_Cull', {
            'Cull Start Time': 'm_flCullStart',
            'Cull End Time': 'm_flCullEnd',
            'Cull Time Exponent': 'm_flCullExp',
            'Cull Percentage': 'm_flCullPerc',
        }),
        'Rotation Spin Roll': ('C_OP_Spin', {
            'spin_rate_degrees': 'm_nSpinRateDegrees',
            'spin_stop_time': 'm_fSpinRateStopTime',
            'spin_rate_min': 'm_nSpinRateMinDegrees',
        }),
        'Rotation Basic': ('C_OP_SpinUpdate', {
        }),
        'Rotation Spin Yaw': ('C_OP_SpinYaw', {
            'yaw_rate_degrees': 'm_nSpinRateDegrees',
            'yaw_stop_time': 'm_fSpinRateStopTime',
            'yaw_rate_min': 'm_nSpinRateMinDegrees',
        }),
        'Radius Scale': ('C_OP_InterpolateRadius', {
            'start_time': 'm_flStartTime',
            'end_time': 'm_flEndTime',
            'radius_start_scale': 'm_flStartScale',
            'radius_end_scale': 'm_flEndScale',
            'ease_in_and_out': 'm_bEaseInAndOut',
            'scale_bias': 'm_flBias',
        }),
        'Color Fade': ('C_OP_ColorInterpolate', {
            'color_fade': 'm_ColorFade',
            'fade_start_time': 'm_flFadeStartTime',
            'fade_end_time': 'm_flFadeEndTime',
            'ease_in_and_out': 'm_bEaseInOut',
            'output field': 'm_nFieldOutput',
        }),
        'Movement Lock to Control Point': ('C_OP_PositionLock', {
            'control_point_number': 'm_nControlPointNumber',
            'start_fadeout_min': 'm_flStartTime_min',
            'start_fadeout_max': 'm_flStartTime_max',
            'start_fadeout_exponent': 'm_flStartTime_exp',
            'end_fadeout_min': 'm_flEndTime_min',
            'end_fadeout_max': 'm_flEndTime_max',
            'end_fadeout_exponent': 'm_flEndTime_exp',
            'distance fade range': 'm_flRange',
            'lock rotation': 'm_bLockRot',
        }),
        'Color Light from Control Point': ('C_OP_ControlpointLight', {
            'Light 1 Control Point': 'm_nControlPoint1',
            'Light 1 Control Point Offset': 'm_vecCPOffset1',
            'Light 1 Type 0=Point 1=Spot': 'm_bLightType1',
            'Light 1 Color': 'm_LightColor1',
            'Light 1 Dynamic Light': 'm_bLightDynamic1',
            'Light 1 Direction': ObjectP('m_LightNode1', 'm_Direction'),
            'Light 1 50% Distance': 'm_LightFiftyDist1',
            'Light 1 0% Distance': 'm_LightZeroDist1',
            'Light 1 Spot Inner Cone': ObjectP('m_LightNode1', 'm_Theta'),
            'Light 1 Spot Outer Cone': ObjectP('m_LightNode1', 'm_Phi'),
            'Light 2 Control Point': 'm_nControlPoint2',
            'Light 2 Control Point Offset': 'm_vecCPOffset2',
            'Light 2 Type 0=Point 1=Spot': 'm_bLightType2',
            'Light 2 Color': 'm_LightColor2',
            'Light 2 Dynamic Light': 'm_bLightDynamic2',
            'Light 2 Direction': ObjectP('m_LightNode2', 'm_Direction'),
            'Light 2 50% Distance': 'm_LightFiftyDist2',
            'Light 2 0% Distance': 'm_LightZeroDist2',
            'Light 2 Spot Inner Cone': ObjectP('m_LightNode2', 'm_Theta'),
            'Light 2 Spot Outer Cone': ObjectP('m_LightNode2', 'm_Phi'),
            'Light 3 Control Point': 'm_nControlPoint3',
            'Light 3 Control Point Offset': 'm_vecCPOffset3',
            'Light 3 Type 0=Point 1=Spot': 'm_bLightType3',
            'Light 3 Color': 'm_LightColor3',
            'Light 3 Dynamic Light': 'm_bLightDynamic3',
            'Light 3 Direction': ObjectP('m_LightNode3', 'm_Direction'),
            'Light 3 50% Distance': 'm_LightFiftyDist3',
            'Light 3 0% Distance': 'm_LightZeroDist3',
            'Light 3 Spot Inner Cone': ObjectP('m_LightNode3', 'm_Theta'),
            'Light 3 Spot Outer Cone': ObjectP('m_LightNode3', 'm_Phi'),
            'Light 4 Control Point': 'm_nControlPoint4',
            'Light 4 Control Point Offset': 'm_vecCPOffset4',
            'Light 4 Type 0=Point 1=Spot': 'm_bLightType4',
            'Light 4 Color': 'm_LightColor4',
            'Light 4 Dynamic Light': 'm_bLightDynamic4',
            'Light 4 Direction': ObjectP('m_LightNode4', 'm_Direction'),
            'Light 4 50% Distance': 'm_LightFiftyDist4',
            'Light 4 0% Distance': 'm_LightZeroDist4',
            'Light 4 Spot Inner Cone': ObjectP('m_LightNode4', 'm_Theta'),
            'Light 4 Spot Outer Cone': ObjectP('m_LightNode4', 'm_Phi'),
            'Initial Color Bias': 'm_flScale',
            'Clamp Minimum Light Value to Initial Color': 'm_bClampLowerRange',
            'Clamp Maximum Light Value to Initial Color': 'm_bClampUpperRange',
            'Compute Normals From Control Points': 'm_bUseNormal',
            'Half-Lambert Normals': 'm_bUseHLambert',
        }),
        'Set child control points from particle positions': ('C_OP_SetChildControlPoints', {
            'Group ID to affect': 'm_nChildGroupID',
            'First control point to set': 'm_nFirstControlPoint',
            '# of control points to set': 'm_nNumControlPoints',
            'first particle to copy': 'm_nFirstSourcePoint',
            'set orientation': 'm_bSetOrientation',
        }),
        'Set control points from particle positions': ('C_OP_SetControlPointsToParticle', {
            'First control point to set': 'm_nFirstControlPoint',
            '# of control points to set': 'm_nNumControlPoints',
            'first particle to copy': 'm_nFirstSourcePoint',
            'set orientation': 'm_bSetOrientation',
        }),
        'Set per child control point from particle positions': ('C_OP_SetPerChildControlPoint', {
            'Group ID to affect': 'm_nChildGroupID',
            'control point to set': 'm_nFirstControlPoint',
            '# of children to set': 'm_nNumControlPoints',
            'first particle to copy': 'm_nFirstSourcePoint',
            'set orientation': 'm_bSetOrientation',
        }),
        'Set Control Point Positions': ('C_OP_SetControlPointPositions', {
            'First Control Point Number': 'm_nCP1',
            'First Control Point Parent': 'm_nCP1Parent',
            'First Control Point Location': 'm_vecCP1Pos',
            'Second Control Point Number': 'm_nCP2',
            'Second Control Point Parent': 'm_nCP2Parent',
            'Second Control Point Location': 'm_vecCP2Pos',
            'Third Control Point Number': 'm_nCP3',
            'Third Control Point Parent': 'm_nCP3Parent',
            'Third Control Point Location': 'm_vecCP3Pos',
            'Fourth Control Point Number': 'm_nCP4',
            'Fourth Control Point Parent': 'm_nCP4Parent',
            'Fourth Control Point Location': 'm_vecCP4Pos',
            'Set positions in world space': 'm_bUseWorldLocation',
            'Control Point to offset positions from': 'm_nHeadLocation',
        }),
        'Movement Dampen Relative to Control Point': ('C_OP_DampenToCP', {
            'control_point_number': 'm_nControlPointNumber',
            'falloff range': 'm_flRange',
            'dampen scale': 'm_flScale',
        }),
        'Remap Distance Between Two Control Points to Scalar': ('C_OP_DistanceBetweenCPs', {
            'distance minimum': 'm_flInputMin',
            'distance maximum': 'm_flInputMax',
            'output field': 'm_nFieldOutput',
            'output minimum': 'm_flOutputMin',
            'output maximum': 'm_flOutputMax',
            'starting control point': 'm_nStartCP',
            'ending control point': 'm_nEndCP',
            'ensure line of sight': 'm_bLOS',
            'LOS collision group': 'm_CollisionGroupName',
            'Maximum Trace Length': 'm_flMaxTraceLength',
            'LOS Failure Scalar': 'm_flLOSScale',
            'output is scalar of initial random range': BoolToSetKV('m_nSetMethod', "PARTICLE_SET_SCALE_CURRENT_VALUE"),#'m_bScaleInitialRange',
            'output is scalar of current value': BoolToSetKV('m_nSetMethod', "PARTICLE_SET_SCALE_INITIAL_VALUE"),#'m_bScaleCurrent',
        }),
        'Remap Distance Between Two Control Points to CP': ('C_OP_DistanceBetweenCPsToCP', {
            'distance minimum': 'm_flInputMin',
            'distance maximum': 'm_flInputMax',
            'output control point': 'm_nOutputCP',
            'output control point field': 'm_nOutputCPField',
            'output minimum': 'm_flOutputMin',
            'output maximum': 'm_flOutputMax',
            'starting control point': 'm_nStartCP',
            'ending control point': 'm_nEndCP',
            'ensure line of sight': 'm_bLOS',
            'LOS collision group': 'm_CollisionGroupName',
            'Maximum Trace Length': 'm_flMaxTraceLength',
            'LOS Failure Scale': 'm_flLOSScale',
        }),
        'Remap Percentage Between Two Control Points to Scalar': ('C_OP_PercentageBetweenCPs', {
            'percentage minimum': 'm_flInputMin',
            'percentage maximum': 'm_flInputMax',
            'output field': 'm_nFieldOutput',
            'output minimum': 'm_flOutputMin',
            'output maximum': 'm_flOutputMax',
            'starting control point': 'm_nStartCP',
            'ending control point': 'm_nEndCP',
            'output is scalar of initial random range': BoolToSetKV('m_nSetMethod', "PARTICLE_SET_SCALE_CURRENT_VALUE"),#'m_bScaleInitialRange',
            'output is scalar of current value': BoolToSetKV('m_nSetMethod', "PARTICLE_SET_SCALE_INITIAL_VALUE"),#'m_bScaleCurrent',
            'only active within input range': 'm_bActiveRange',
            'treat distance between points as radius': 'm_bRadialCheck',
        }),
        'Remap Percentage Between Two Control Points to Vector': ('C_OP_PercentageBetweenCPsVector', {
            'percentage minimum': 'm_flInputMin',
            'percentage maximum': 'm_flInputMax',
            'output field': 'm_nFieldOutput',
            'output minimum': 'm_vecOutputMin',
            'output maximum': 'm_vecOutputMax',
            'starting control point': 'm_nStartCP',
            'ending control point': 'm_nEndCP',
            'output is scalar of initial random range': BoolToSetKV('m_nSetMethod', "PARTICLE_SET_SCALE_CURRENT_VALUE"),#'m_bScaleInitialRange',
            'output is scalar of current value': BoolToSetKV('m_nSetMethod', "PARTICLE_SET_SCALE_INITIAL_VALUE"),#'m_bScaleCurrent',
            'only active within input range': 'm_bActiveRange',
            'treat distance between points as radius': 'm_bRadialCheck',
        }),
        'Remap Distance to Control Point to Scalar': ('C_OP_DistanceToCP', {
            'distance minimum': 'm_flInputMin',
            'distance maximum': 'm_flInputMax',
            'output field': 'm_nFieldOutput',
            'output minimum': 'm_flOutputMin',
            'output maximum': 'm_flOutputMax',
            'control point': 'm_nStartCP',
            'ensure line of sight': 'm_bLOS',
            'LOS collision group': 'm_CollisionGroupName',
            'Maximum Trace Length': 'm_flMaxTraceLength',
            'LOS Failure Scalar': 'm_flLOSScale',
            'output is scalar of initial random range': BoolToSetKV('m_nSetMethod', "PARTICLE_SET_SCALE_CURRENT_VALUE"),#'m_bScaleInitialRange',
            'output is scalar of current value': BoolToSetKV('m_nSetMethod', "PARTICLE_SET_SCALE_INITIAL_VALUE"),#'m_bScaleCurrent',
            'only active within specified distance': 'm_bActiveRange',
        }),
        'Set Control Point To Player': ('C_OP_SetControlPointToPlayer', {
            'Control Point Number': 'm_nCP1',
            'Control Point Offset': 'm_vecCP1Pos',
            'Use Eye Orientation': 'm_bOrientToEyes',
        }),
        'Movement Lerp to Hitbox': ('C_OP_MoveToHitbox', {
            'control point number': 'm_nControlPointNumber',
            'lifetime lerp start': 'm_flLifeTimeLerpStart',
            'lifetime lerp end': 'm_flLifeTimeLerpEnd',
            'hitbox set': 'm_HitboxSetName',
        }),
        'Movement Lock to Bone': ('C_OP_LockToBone', {
            'control_point_number': 'm_nControlPointNumber',
            'lifetime fade start': 'm_flLifeTimeFadeStart',
            'lifetime fade end': 'm_flLifeTimeFadeEnd',
            'hitbox set': 'm_HitboxSetName',
        }),
        'Set CP Offset to CP Percentage Between Two Control Points': ('C_OP_CPOffsetToPercentageBetweenCPs', {
            'percentage minimum': 'm_flInputMin',
            'percentage maximum': 'm_flInputMax',
            'percentage bias': 'm_flInputBias',
            'starting control point': 'm_nStartCP',
            'ending control point': 'm_nEndCP',
            'offset control point': 'm_nOffsetCP',
            'input control point': 'm_nInputCP',
            'output control point': 'm_nOuputCP',
            'offset amount': 'm_vecOffset',
            'treat distance between points as radius': 'm_bRadialCheck',
            'treat offset as scale of total distance': 'm_bScaleOffset',
        }),
        'Cull when crossing plane': ('C_OP_PlaneCull', {
            'Control Point for point on plane': 'm_nPlaneControlPoint',
            'Cull plane offset': 'm_flPlaneOffset',
            'Plane Normal': 'm_vecPlaneDirection',
        }),
        'Cull when crossing sphere': ('C_OP_DistanceCull', {
            'Control Point': 'm_nControlPoint',
            'Cull Distance': 'm_flDistance',
            'Control Point offset': 'm_vecPointOffset',
            'Cull inside instead of outside': 'm_bCullInside',
        }),
        'Cull relative to model': ('C_OP_ModelCull', {
            'control_point_number': 'm_nControlPointNumber',
            'use only bounding box': 'm_bBoundBox',
            'cull outside instead of inside': 'm_bCullOutside',
            'hitbox set': 'm_HitboxSetName',
        }),
        "Set Control Point To Particles' Center": ('C_OP_SetControlPointToCenter', {
            'Control Point Number to Set': 'm_nCP1',
            'Center Offset': 'm_vecCP1Pos',
        }),
        'Movement Match Particle Velocities': ('C_OP_VelocityMatchingForce', {
            'Direction Matching Strength': 'm_flDirScale',
            'Speed Matching Strength': 'm_flSpdScale',
            'Control Point to Broadcast Speed and Direction To': 'm_nCPBroadcast',
        }),
        'Movement Maintain Offset': ('C_OP_MovementMaintainOffset', {
            'Local Space CP': 'm_nCP',
            'Desired Offset': 'm_vecOffset',
            'Scale by Radius': 'm_bRadiusScale',
        }),
        'Movement Place On Ground': ('C_OP_MovementPlaceOnGround', {
            'offset': 'm_flOffset',
            'kill on no collision': 'm_bKill',
            'include water': 'm_bIncludeWater',
            'max trace length': 'm_flMaxTraceLength',
            'trace offset': 'm_flTraceOffset',
            'collision group': 'm_CollisionGroupName',
            'reference CP 1': 'm_nRefCP1',
            'reference CP 2': 'm_nRefCP2',
            'CP movement tolerance': 'm_flTolerance',
            'interpolation rate': 'm_flLerpRate',
            'interploation distance tolerance cp': 'm_nLerpCP',
        }),
        'Inherit Attribute From Parent Particle': ('C_OP_InheritFromParentParticlesV2', { # V2
            # inverse booltosetkv
            'run for killed parent particles': lambda v: None if not v else ('m_nMissingParentBehavior', "MISSING_PARENT_KILL"),#'m_bRunForParentApplyKillList', #
            'Inherited Field': 'm_nFieldOutput',
            'Scale': 'm_flScale',
            'Random Parent Particle Distribution': 'm_bRandomDistribution',
            'Particle Increment Amount': 'm_nIncrement',
        }),
        'Rotation Orient to 2D Direction': ('C_OP_OrientTo2dDirection', {
            'Rotation Offset': 'm_flRotOffset',
            'Spin Strength': 'm_flSpinStrength',
            'rotation field': 'm_nFieldOutput',
        }),
        'Restart Effect after Duration': ('C_OP_RestartAfterDuration', {
            'Minimum Restart Time': 'm_flDurationMin',
            'Maximum Restart Time': 'm_flDurationMax',
            'Control Point to Scale Duration': 'm_nCP',
            'Control Point Field X/Y/Z': 'm_nCPField',
            'Only Restart Children': 'm_bOnlyChildren',
            'Child Group ID': 'm_nChildGroupID',
        }),
        'Stop Effect after Duration': ('C_OP_StopAfterCPDuration', {
            'Duration at which to Stop': 'm_flDuration',
            'Control Point to Scale Duration': 'm_nCP',
            'Control Point Field X/Y/Z': 'm_nCPField',
            'Destroy All Particles Immediately': 'm_bDestroyImmediately',
            'Play End Cap Effect': 'm_bPlayEndCap',
        }),
        'Rotation Orient Relative to CP': ('C_OP_Orient2DRelToCP', {
            'Rotation Offset': 'm_flRotOffset',
            'Spin Strength': 'm_flSpinStrength',
            'Control Point': 'm_nCP',
            'rotation field': 'm_nFieldOutput',
        }),
        'Set Control Point Rotation': ('C_OP_SetControlPointRotation', {
            'Rotation Axis': 'm_vecRotAxis',
            'Rotation Rate': 'm_flRotRate',
            'Control Point': 'm_nCP',
            'Local Space Control Point': 'm_nLocalCP',
        }),
        'Movement Rotate Particle Around Axis': ('C_OP_MovementRotateParticleAroundAxis', {
            'Rotation Axis': 'm_vecRotAxis',
            'Rotation Rate': 'm_flRotRate',
            'Control Point': 'm_nCP',
            'Use Local Space': 'm_bLocalSpace',
        }),
        'Rotate Vector Random': ('C_OP_RotateVector', {
            'output field': 'm_nFieldOutput',
            'Rotation Axis Min': 'm_vecRotAxisMin',
            'Rotation Axis Max': 'm_vecRotAxisMax',
            'Rotation Rate Min': 'm_flRotRateMin',
            'Rotation Rate Max': 'm_flRotRateMax',
            'Normalize Ouput': 'm_bNormalize',
        }),
        'Movement Max Velocity': ('C_OP_MaxVelocity', {
            'Maximum Velocity': 'm_flMaxVelocity',
            'Override Max Velocity from this CP': 'm_nOverrideCP',
            'Override CP field': 'm_nOverrideCPField',
        }),
        'Movement Lag Compensation': ('C_OP_LagCompensation', {
            'Desired Velocity CP': 'm_nDesiredVelocityCP',
            'Desired Velocity CP Field Override(for speed only)': 'm_nDesiredVelocityCPField',
            'Latency CP': 'm_nLatencyCP',
            'Latency CP field': 'm_nLatencyCPField',
        }),
        'Movement Maintain Position Along Path': ('C_OP_MaintainSequentialPath', {
            'maximum distance': 'm_fMaxDistance',
            **(_m_PathParams:={'bulge': ObjectP('m_PathParams', 'm_flBulge'),
            'start control point number': ObjectP('m_PathParams', 'm_nStartControlPointNumber'),
            'end control point number': ObjectP('m_PathParams', 'm_nEndControlPointNumber'),
            'bulge control 0=random 1=orientation of start pnt 2=orientation of end point': ObjectP('m_PathParams', 'm_nBulgeControl'),
            'mid point position': ObjectP('m_PathParams', 'm_flMidPoint'),}),
            'particles to map from start to end': 'm_flNumToAssign',
            'restart behavior (0 = bounce, 1 = loop )': 'm_bLoop',
            'cohesion strength': 'm_flCohesionStrength',
            'use existing particle count': 'm_bUseParticleCount',
            'control point movement tolerance': 'm_flTolerance',
        }),
        'Movement Lock to Saved Position Along Path': ('C_OP_LockToSavedSequentialPathV2', { # V2
            'Use sequential CP pairs between start and end point': 'm_bCPPairs',
            **_m_PathParams,
        }),
        'Remap Dot Product to Scalar': ('C_OP_RemapDotProductToScalar', {
            'use particle velocity for first input': 'm_bUseParticleVelocity',
            'first input control point': 'm_nInputCP1',
            'second input control point': 'm_nInputCP2',
            'input minimum (-1 to 1)': 'm_flInputMin',
            'input maximum (-1 to 1)': 'm_flInputMax',
            'output field': 'm_nFieldOutput',
            'output minimum': 'm_flOutputMin',
            'output maximum': 'm_flOutputMax',
            'output is scalar of initial random range': BoolToSetKV('m_nSetMethod', "PARTICLE_SET_SCALE_CURRENT_VALUE"),#'m_bScaleInitialRange',
            'output is scalar of current value': BoolToSetKV('m_nSetMethod', "PARTICLE_SET_SCALE_INITIAL_VALUE"),#'m_bScaleCurrent',
            'only active within specified input range': 'm_bActiveRange',
        }),
        'Remap Control Point to Scalar': ('C_OP_RemapCPtoScalar', {
            'emitter lifetime start time (seconds)': 'm_flStartTime',
            'emitter lifetime end time (seconds)': 'm_flEndTime',
            'input control point number': 'm_nCPInput',
            'input minimum': 'm_flInputMin',
            'input maximum': 'm_flInputMax',
            'input field 0-2 X/Y/Z': 'm_nField',
            'output field': 'm_nFieldOutput',
            'output minimum': 'm_flOutputMin',
            'output maximum': 'm_flOutputMax',
            'output is scalar of initial random range': BoolToSetKV('m_nSetMethod', "PARTICLE_SET_SCALE_CURRENT_VALUE"),#'m_bScaleInitialRange',
            'output is scalar of current value': BoolToSetKV('m_nSetMethod', "PARTICLE_SET_SCALE_INITIAL_VALUE"),#'m_bScaleCurrent',
        }),
        'Normal Lock to Control Point': ('C_OP_NormalLock', {
            'control_point_number': 'm_nControlPointNumber',
        }),
        'Set Control Point to Impact Point': ('C_OP_SetControlPointToImpactPoint', {
            'Control Point to Set': 'm_nCPOut',
            'Control Point to Trace From': 'm_nCPIn',
            'Trace Direction Override': 'm_vecTraceDir',
            'Trace Update Rate': 'm_flUpdateRate',
            'Max Trace Length': 'm_flTraceLength',
            'Offset End Point Amount': 'm_flOffset',
            'trace collision group': 'm_CollisionGroupName',
        }),
        'Remap Control Point to Vector': ('C_OP_RemapCPtoVector', {
            'emitter lifetime start time (seconds)': 'm_flStartTime',
            'emitter lifetime end time (seconds)': 'm_flEndTime',
            'input control point number': 'm_nCPInput',
            'input minimum': 'm_vInputMin',
            'input maximum': 'm_vInputMax',
            'output field': 'm_nFieldOutput',
            'output minimum': 'm_vOutputMin',
            'output maximum': 'm_vOutputMax',
            'output is scalar of initial random range': BoolToSetKV('m_nSetMethod', "PARTICLE_SET_SCALE_CURRENT_VALUE"),#'m_bScaleInitialRange',
            'output is scalar of current value': BoolToSetKV('m_nSetMethod', "PARTICLE_SET_SCALE_INITIAL_VALUE"),#'m_bScaleCurrent',
            'offset position': 'm_bOffset',
            'accelerate position': 'm_bAccelerate',
            'local space CP': 'm_nLocalSpaceCP',
        }),
        'Remap Velocity to Vector': ('C_OP_RemapVelocityToVector', {
            'output field': 'm_nFieldOutput',
            'normalize': 'm_bNormalize',
            'scale factor': 'm_flScale',
        }),
        'Remap CP Velocity to Vector': ('C_OP_RemapCPVelocityToVector', {
            'output field': 'm_nFieldOutput',
            'control point': 'm_nControlPoint',
            'normalize': 'm_bNormalize',
            'scale factor': 'm_flScale',
        }),
        'Set CP Orientation to CP Direction': ('C_OP_SetCPOrientationToDirection', {
            'input control point': 'm_nInputControlPoint',
            'output control point': 'm_nOutputControlPoint',
        }),
        'Remap Direction to CP to Vector': ('C_OP_RemapDirectionToCPToVector', {
            'control point': 'm_nCP',
            'output field': 'm_nFieldOutput',
            'normalize': 'm_bNormalize',
            'offset axis': 'm_vecOffsetAxis',
            'offset rotation': 'm_flOffsetRot',
            'scale factor': 'm_flScale',
        }),
        'Normalize Vector': ('C_OP_NormalizeVector', {
            'output field': 'm_nFieldOutput',
            'scale factor': 'm_flScale',
        }),
        'Remap Control Point Direction to Vector': ('C_OP_RemapControlPointDirectionToVector', {
            'output field': 'm_nFieldOutput',
            'control point number': 'm_nControlPointNumber',
            'scale factor': 'm_flScale',
        }),
        #'Remap Distance to Control Point to Vector': NotImplemented, # maybe C_OP_RemapDistanceToLineSegmentToVector
        #'Distance to Control Points Scale': NotImplemented,
        'Movement Follow CP': ('', {
            'update particle life time': '',
            'lerp to CP radius speed': '',
            'catch up speed': '',
            'maximum end control point': '',
        }),
        'spin': ('C_OP_Spin', {
            'spin_rate': 'm_nSpinRateDegrees',
            'spin_stop_time': 'm_fSpinRateStopTime',
        }),
    }),

    'initializers': ('m_Initializers', {
        'Position Along Ring': ('C_INIT_RingWave', {        
            'control point number': 'm_nControlPointNumber',
            'initial radius': 'm_flInitialRadius',
            'thickness': 'm_flThickness',
            'min initial speed': 'm_flInitialSpeedMin',     
            'max initial speed': 'm_flInitialSpeedMax',     
            'yaw': 'm_flYaw',
            'roll': 'm_flRoll',
            'pitch': 'm_flPitch',
            'even distribution': 'm_bEvenDistribution',
            'even distribution count': 'm_flParticlesPerOrbit',
            'XY velocity only': 'm_bXYVelocityOnly',
            'Override CP (X/Y/Z *= Radius/Thickness/Speed)': 'm_nOverrideCP',
            'Override CP 2 (X/Y/Z *= Pitch/Yaw/Roll)': 'm_nOverrideCP2',
        }),
        'Position Along Epitrochoid': ('C_INIT_CreateInEpitrochoid', {
            'control point number': 'm_nControlPointNumber',
            'first dimension 0-2 (-1 disables)': 'm_nComponent1',
            'second dimension 0-2 (-1 disables)': 'm_nComponent2',
            'radius 1': 'm_flRadius1',
            'radius 2': 'm_flRadius2',
            'point offset': 'm_flOffset',
            'particle density': 'm_flParticleDensity',
            'use particle count instead of creation time': 'm_bUseCount',
            'local space': 'm_bUseLocalCoords',
            'offset from existing position': 'm_bOffsetExistingPos',
            'scale from conrol point (radius 1/radius 2/offset)': 'm_nScaleCP',
        }),
        'Position on Model Random': ('C_INIT_CreateOnModel', {
            'control_point_number': 'm_nControlPointNumber',
            'force to be inside model': 'm_nForceInModel',
            'hitbox scale': 'm_flHitBoxScale',
            'model hitbox scale': 'm_flHitBoxScale',
            'direction bias': 'm_vecDirectionBias',
            'desired hitbox': 'm_nDesiredHitbox',
            'hitbox set': 'm_HitboxSetName',
        }),
        'Set Hitbox to Closest Hitbox': ('C_INIT_SetHitboxToClosest', {
            'control_point_number': 'm_nControlPointNumber',
            'model hitbox scale': 'm_flHitBoxScale',
            'desired hitbox': 'm_nDesiredHitbox',
            'hitbox set': 'm_HitboxSetName',
        }),
        'Set Hitbox Position on Model': ('C_INIT_SetHitboxToModel', {
            'control_point_number': 'm_nControlPointNumber',
            'force to be inside model': 'm_nForceInModel',
            'model hitbox scale': 'm_flHitBoxScale',
            'direction bias': 'm_vecDirectionBias',
            'desired hitbox': 'm_nDesiredHitbox',
            'hitbox set': 'm_HitboxSetName',
            'maintain existing hitbox': 'm_bMaintainHitbox',
        }),
        'Position Within Sphere Random': ('C_INIT_CreateWithinSphere', {
            'distance_min': 'm_fRadiusMin',
            'distance_max': 'm_fRadiusMax',
            'distance_bias': 'm_vecDistanceBias',
            'distance_bias_absolute_value': 'm_vecDistanceBiasAbs',
            'bias in local system': 'm_bLocalCoords',
            'control_point_number': 'm_nControlPointNumber',
            'speed_min': 'm_fSpeedMin',
            'speed_max': 'm_fSpeedMax',
            'speed_random_exponent': 'm_fSpeedRandExp',
            'speed_in_local_coordinate_system_min': 'm_LocalCoordinateSystemSpeedMin',
            'speed_in_local_coordinate_system_max': 'm_LocalCoordinateSystemSpeedMax',
            'randomly distribute to highest supplied Control Point': 'm_bUseHighestEndCP',
            'randomly distribution growth time': 'm_flEndCPGrowthTime',
            'scale cp (distance/speed/local speed)': 'm_nScaleCP',
        }),
        'Position Within Box Random': ('C_INIT_CreateWithinBox', {
            'min': 'm_vecMin',
            'max': 'm_vecMax',
            'control point number': 'm_nControlPointNumber',
            'use local space': 'm_bLocalSpace',
        }),
        'Position Modify Offset Random': ('C_INIT_PositionOffset', {
            'control_point_number': 'm_nControlPointNumber',
            'offset min': 'm_OffsetMin',
            'offset max': 'm_OffsetMax',
            'offset in local space 0/1': 'm_bLocalCoords',
            'offset proportional to radius 0/1': 'm_bProportional',
        }),
        'Position Modify Place On Ground': ('C_INIT_PositionPlaceOnGround', {
            'offset': 'm_flOffset',
            'kill on no collision': 'm_bKill',
            'include water': 'm_bIncludeWater',
            'set normal': 'm_bSetNormal',
            'max trace length': 'm_flMaxTraceLength',
            'collision group': 'm_CollisionGroupName',
        }),
        'Velocity Random': ('C_INIT_VelocityRandom', {
            'control_point_number': 'm_nControlPointNumber',
            'random_speed_min': 'm_fSpeedMin',
            'random_speed_max': 'm_fSpeedMax',
            'speed_in_local_coordinate_system_min': 'm_LocalCoordinateSystemSpeedMin',
            'speed_in_local_coordinate_system_max': 'm_LocalCoordinateSystemSpeedMax',
        }),
        'Velocity Noise': ('C_INIT_InitialVelocityNoise', {
            'Control Point Number': 'm_nControlPointNumber',
            'Time Noise Coordinate Scale': 'm_flNoiseScale',
            'Spatial Noise Coordinate Scale': 'm_flNoiseScaleLoc',
            'Time Coordinate Offset': 'm_flOffset',
            'Spatial Coordinate Offset': 'm_vecOffsetLoc',
            'Absolute Value': 'm_vecAbsVal',
            'Invert Abs Value': 'm_vecAbsValInv',
            'output minimum': 'm_vecOutputMin',
            'output maximum': 'm_vecOutputMax',
            'Apply Velocity in Local Space (0/1)': 'm_bLocalSpace',
        }),
        'Lifetime Random': ('C_INIT_RandomLifeTime', {
            'lifetime_min': 'm_fLifetimeMin',
            'lifetime_max': 'm_fLifetimeMax',
            'lifetime_random_exponent': 'm_fLifetimeRandExponent',
        }),
        'Scalar Random': ('C_INIT_RandomScalar', {
            'min': 'm_flMin',
            'max': 'm_flMax',
            'exponent': 'm_flExponent',
            'output field': 'm_nFieldOutput',
        }),
        'Vector Random': ('C_INIT_RandomVector', {
            'min': 'm_vecMin',
            'max': 'm_vecMax',
            'output field': 'm_nFieldOutput',
        }),
        'Vector Component Random': ('C_INIT_RandomVectorComponent', {
            'min': 'm_flMin',
            'max': 'm_flMax',
            'component 0/1/2 X/Y/Z': 'm_nComponent',
            'output field': 'm_nFieldOutput',
        }),
        'Radius Random': ('C_INIT_RandomRadius', {
            'radius_min': 'm_flRadiusMin',
            'radius_max': 'm_flRadiusMax',
            'radius_random_exponent': 'm_flRadiusRandExponent',
        }),
        'Alpha Random': ('C_INIT_RandomAlpha', {
            'alpha_min': 'm_nAlphaMin',
            'alpha_max': 'm_nAlphaMax',
            'alpha_random_exponent': 'm_flAlphaRandExponent',
        }),
        'Rotation Random': ('C_INIT_RandomRotation', {
            'rotation_initial': 'm_flDegrees',
            'rotation_offset_min': 'm_flDegreesMin',
            'rotation_offset_max': 'm_flDegreesMax',
            'rotation_random_exponent': 'm_flRotationRandExponent',
            'randomly_flip_direction': 'm_bRandomlyFlipDirection',
        }),
        'Rotation Speed Random': ('C_INIT_RandomRotationSpeed', {
            'rotation_speed_constant': 'm_flDegrees',
            'rotation_speed_random_min': 'm_flDegreesMin',
            'rotation_speed_random_max': 'm_flDegreesMax',
            'rotation_speed_random_exponent': 'm_flRotationRandExponent',
            'randomly_flip_direction': 'm_bRandomlyFlipDirection',
        }),
        'Rotation Yaw Random': ('C_INIT_RandomYaw', {
            'yaw_initial': 'm_flDegrees',
            'yaw_offset_min': 'm_flDegreesMin',
            'yaw_offset_max': 'm_flDegreesMax',
            'yaw_random_exponent': 'm_flRotationRandExponent',
        }),
        'Color Random': ('C_INIT_RandomColor', {
            'color1': 'm_ColorMin',
            'color2': 'm_ColorMax',
            'tint_perc': 'm_flTintPerc',
            'tint control point': 'm_nTintCP',
            'tint clamp min': 'm_TintMin',
            'tint clamp max': 'm_TintMax',
            'tint update movement threshold': 'm_flUpdateThreshold',
            'tint blend mode': 'm_nTintBlendMode',  # dmx:int kv3:str
            'light amplification amount': 'm_flLightAmplification',
            'output field': 'm_nFieldOutput',
        }),
        'Color Lit Per Particle': ('C_INIT_ColorLitPerParticle', {
            'color1': 'm_ColorMin',
            'color2': 'm_ColorMax',
            'light bias': 'm_flTintPerc',
            'tint clamp min': 'm_TintMin',
            'tint clamp max': 'm_TintMax',
            'tint blend mode': 'm_nTintBlendMode',
            'light amplification amount': 'm_flLightAmplification',
        }),
        'Trail Length Random': ('C_INIT_RandomTrailLength', {
            'length_min': 'm_flMinLength',
            'length_max': 'm_flMaxLength',
            'length_random_exponent': 'm_flLengthRandExponent',
        }),
        'Sequence Random': ('C_INIT_RandomSequence', {
            'sequence_min': 'm_nSequenceMin',
            'sequence_max': 'm_nSequenceMax',
            'shuffle': 'm_bShuffle',
            'linear': 'm_bLinear',
        }),
        'Sequence From Control Point': ('C_INIT_SequenceFromCP', {
            'control point': 'm_nCP',
            'per particle spatial offset': 'm_vecOffset',
            'offset propotional to radius': 'm_bRadiusScale',
        }),
        'Position Modify Warp Random': ('C_INIT_PositionWarp', {
            'control point number': 'm_nControlPointNumber',
            'warp min': 'm_vecWarpMin',
            'warp max': 'm_vecWarpMax',
            'warp transition time (treats min/max as start/end sizes)': 'm_flWarpTime',
            'warp transition start time': 'm_flWarpStartTime',
            'reverse warp (0/1)': 'm_bInvertWarp',
            'use particle count instead of time': 'm_bUseCount',
        }),
        'Remap Noise to Scalar': ('C_INIT_CreationNoise', {
            'Time Noise Coordinate Scale': 'm_flNoiseScale',
            'time noise coordinate scale': 'm_flNoiseScale',
            'spatial noise coordinate scale': 'm_flNoiseScaleLoc',
            'output field': 'm_nFieldOutput',
            'time coordinate offset': 'm_flOffset',
            'spatial coordinate offset': 'm_vecOffsetLoc',
            'absolute value': 'm_bAbsVal',
            'invert absolute value': 'm_bAbsValInv',
            'output minimum': 'm_flOutputMin',
            'output maximum': 'm_flOutputMax',
            'world time noise coordinate scale': 'm_flWorldTimeScale',
        }),
        'Position Along Path Random': ('C_INIT_CreateAlongPath', {
            'maximum distance': 'm_fMaxDistance',
            **_m_PathParams,
            'randomly select sequential CP pairs between start and end points': 'm_bUseRandomCPs',
        }),
        'Move Particles Between 2 Control Points': ('C_INIT_MoveBetweenPoints', {
            'minimum speed': 'm_flSpeedMin',
            'maximum speed': 'm_flSpeedMax',
            'end spread': 'm_flEndSpread',
            'start offset': 'm_flStartOffset',
            'end offset': 'm_flEndOffset',
            'bias lifetime by trail length': 'm_bTrailBias',
            'end control point': 'm_nEndControlPointNumber',
        }),
        'Remap Initial Scalar': ('C_INIT_RemapScalar', {
            'emitter lifetime start time (seconds)': 'm_flStartTime',
            'emitter lifetime end time (seconds)': 'm_flEndTime',
            'input field': 'm_nFieldInput',
            'input minimum': 'm_flInputMin',
            'input maximum': 'm_flInputMax',
            'output field': 'm_nFieldOutput',
            'output minimum': 'm_flOutputMin',
            'output maximum': 'm_flOutputMax',
            'output is scalar of initial random range': BoolToSetKV(k='m_nSetMethod', v='PARTICLE_SET_SCALE_CURRENT_VALUE'),
            'only active within specified input range': 'm_bActiveRange',
        }),
        'Remap Particle Count to Scalar': ('C_INIT_RemapParticleCountToScalar', {
            'input minimum': 'm_nInputMin',
            'input maximum': 'm_nInputMax',
            'output field': 'm_nFieldOutput',
            'output minimum': 'm_flOutputMin',
            'output maximum': 'm_flOutputMax',
            'output is scalar of initial random range': BoolToSetKV(k='m_nSetMethod', v='PARTICLE_SET_SCALE_CURRENT_VALUE'),
            'only active within specified input range': 'm_bActiveRange',
        }),
        'Velocity Inherit from Control Point': ('C_INIT_InheritVelocity', {
            'control point number': 'm_nControlPointNumber',
            'velocity scale': 'm_flVelocityScale',
        }),
        'Velocity Set from Control Point': ('C_INIT_VelocityFromCP', {
            'control point number': 'm_nControlPoint',
            'velocity scale': 'm_flVelocityScale',
            'comparison control point number': 'm_nControlPointCompare',
            'local space control point number': 'm_nControlPointLocal',
            'direction only': 'm_bDirectionOnly',
        }),
        'Lifetime Pre-Age Noise': ('C_INIT_AgeNoise', {
            'time noise coordinate scale': 'm_flNoiseScale',
            'spatial noise coordinate scale': 'm_flNoiseScaleLoc',
            'time coordinate offset': 'm_flOffset',
            'spatial coordinate offset': 'm_vecOffsetLoc',
            'absolute value': 'm_bAbsVal',
            'invert absolute value': 'm_bAbsValInv',
            'start age minimum': 'm_flAgeMin',
            'start age maximum': 'm_flAgeMax',
        }),
        'Lifetime From Sequence': ('C_INIT_SequenceLifeTime', {
            'Frames Per Second': 'm_flFramerate',
        }),
        'Position In CP Hierarchy': ('C_INIT_CreateInHierarchy', {
            'maximum distance': 'm_fMaxDistance',
            'bulge': 'm_flBulgeFactor',
            'start control point number': 'm_nDesiredStartPoint',
            'end control point number': 'm_nDesiredEndPoint',
            'bulge control 0=random 1=orientation of start pnt 2=orientation of end point': 'm_nOrientation',
            'mid point position': 'm_flDesiredMidPoint',
            'growth time': 'm_flGrowthTime',
            'use highest supplied end point': 'm_bUseHighestEndCP',
            'distance_bias': 'm_vecDistanceBias',
            'distance_bias_absolute_value': 'm_vecDistanceBiasAbs',
        }),
        'Remap Scalar to Vector': ('C_INIT_RemapScalarToVector', {
            'emitter lifetime start time (seconds)': 'm_flStartTime',
            'emitter lifetime end time (seconds)': 'm_flEndTime',
            'input field': 'm_nFieldInput',
            'input minimum': 'm_flInputMin',
            'input maximum': 'm_flInputMax',
            'output field': 'm_nFieldOutput',
            'output minimum': 'm_vecOutputMin',
            'output maximum': 'm_vecOutputMax',
            'output is scalar of initial random range': BoolToSetKV(k='m_nSetMethod', v='PARTICLE_SET_SCALE_CURRENT_VALUE'),
            'use local system': 'm_bLocalCoords',
            'control_point_number': 'm_nControlPointNumber',
        }),
        'Offset Vector to Vector': ('C_INIT_OffsetVectorToVector', {
            'input field': 'm_nFieldInput',
            'output field': 'm_nFieldOutput',
            'output offset minimum': 'm_vecOutputMin',
            'output offset maximum': 'm_vecOutputMax',
        }),
        'Position Along Path Sequential': ('C_INIT_CreateSequentialPathV2', { # V2
            'maximum distance': 'm_fMaxDistance',
            **_m_PathParams,
            'particles to map from start to end': 'm_flNumToAssign',
            'restart behavior (0 = bounce, 1 = loop )': 'm_bLoop',
            'Use sequential CP pairs between start and end point': 'm_bCPPairs',
            'Save Offset': 'm_bSaveOffset',
        }),
        'Velocity Repulse from World': ('C_INIT_InitialRepulsionVelocity', {
            'minimum velocity': 'm_vecOutputMin',
            'maximum velocity': 'm_vecOutputMax',
            'collision group': 'm_CollisionGroupName',
            'control_point_number': 'm_nControlPointNumber',
            'Per Particle World Collision Tests': 'm_bPerParticle',
            'Use radius for Per Particle Trace Length': 'm_bPerParticleTR',
            'Offset instead of accelerate': 'm_bTranslate',
            'Offset proportional to radius 0/1': 'm_bProportional',
            'Trace Length': 'm_flTraceLength',
            'Inherit from Parent': 'm_bInherit',
            'control points to broadcast to children (n + 1)': 'm_nChildCP',
            'Child Group ID to affect': 'm_nChildGroupID',
        }),
        'Rotation Yaw Flip Random': ('C_INIT_RandomYawFlip', {
            'Flip Percentage': 'm_flPercent',
        }),
        'Sequence Two Random': ('C_INIT_RandomSecondSequence', {
            'sequence_min': 'm_nSequenceMin',
            'sequence_max': 'm_nSequenceMax',
        }),
        'Remap Control Point to Scalar': ('C_INIT_RemapCPtoScalar', {
            'emitter lifetime start time (seconds)': 'm_flStartTime',
            'emitter lifetime end time (seconds)': 'm_flEndTime',
            'input control point number': 'm_nCPInput',
            'input minimum': 'm_flInputMin',
            'input maximum': 'm_flInputMax',
            'input field 0-2 X/Y/Z': 'm_nField',
            'output field': 'm_nFieldOutput',
            'output minimum': 'm_flOutputMin',
            'output maximum': 'm_flOutputMax',
            'output is scalar of initial random range': BoolToSetKV(k='m_nSetMethod', v='PARTICLE_SET_SCALE_CURRENT_VALUE'),
        }),
        'Remap Control Point to Vector': ('C_INIT_RemapCPtoVector', {
            'emitter lifetime start time (seconds)': 'm_flStartTime',
            'emitter lifetime end time (seconds)': 'm_flEndTime',
            'input control point number': 'm_nCPInput',
            'input minimum': 'm_vInputMin',
            'input maximum': 'm_vInputMax',
            'output field': 'm_nFieldOutput',
            'output minimum': 'm_vOutputMin',
            'output maximum': 'm_vOutputMax',
            'output is scalar of initial random range': BoolToSetKV(k='m_nSetMethod', v='PARTICLE_SET_SCALE_CURRENT_VALUE'),
            'offset position': 'm_bOffset',
            'accelerate position': 'm_bAccelerate',
            'local space CP': 'm_nLocalSpaceCP',
        }),
        'Position From Chaotic Attractor': ('C_INIT_ChaoticAttractor', {
            'Pickover A Parameter': 'm_flAParm',
            'Pickover B Parameter': 'm_flBParm',
            'Pickover C Parameter': 'm_flCParm',
            'Pickover D Parameter': 'm_flDParm',
            'Speed Min': 'm_flSpeedMin',
            'Speed Max': 'm_flSpeedMax',
            'Uniform speed': 'm_bUniformSpeed',
            'Relative Control point number': 'm_nBaseCP',
            'Scale': 'm_flScale',
        }),
        'Position From Parent Particles': ('C_INIT_CreateFromParentParticles', {
            'Inherited Velocity Scale': 'm_flVelocityScale',
            'Random Parent Particle Distribution': 'm_bRandomDistribution',
            'Particle Increment Amount': 'm_nIncrement',
        }),
        'Inherit Initial Value From Parent Particle': ('C_INIT_InheritFromParentParticles', {
            'Inherited Field': 'm_nFieldOutput',
            'Scale': 'm_flScale',
            'Random Parent Particle Distribution': 'm_bRandomDistribution',
            'Particle Increment Amount': 'm_nIncrement',
        }),
        'Remap Initial Distance to Control Point to Scalar': ('C_INIT_DistanceToCPInit', {
            'distance minimum': 'm_flInputMin',
            'distance maximum': 'm_flInputMax',
            'output field': 'm_nFieldOutput',
            'output minimum': 'm_flOutputMin',
            'output maximum': 'm_flOutputMax',
            'control point': 'm_nStartCP',
            'ensure line of sight': 'm_bLOS',
            'LOS collision group': 'm_CollisionGroupName',
            'Maximum Trace Length': 'm_flMaxTraceLength',
            'LOS Failure Scalar': 'm_flLOSScale',
            'output is scalar of initial random range': BoolToSetKV(k='m_nSetMethod', v='PARTICLE_SET_SCALE_CURRENT_VALUE'),
            'only active within specified distance': 'm_bActiveRange',
        }),
        'Lifetime from Time to Impact': ('C_INIT_LifespanFromVelocity', {
            'trace collision group': 'm_CollisionGroupName',
            'maximum trace length': 'm_flMaxTraceLength',
            'trace offset': 'm_flTraceOffset',
            'trace recycle tolerance': 'm_flTraceTolerance',
            'maximum points to cache': 'm_nMaxPlanes',
            'bias distance': 'm_vecComponentScale',
            'collide with water': 'm_bIncludeWater',
        }),
        'Position from Parent Cache': ('C_INIT_CreateFromPlaneCache', {
            'Local Offset Min': 'm_vecOffsetMin',
            'Local Offset Max': 'm_vecOffsetMax',
            'Set Normal': 'm_bUseNormal',
        }),
        'Cull relative to model': ('C_INIT_ModelCull', {
            'control_point_number': 'm_nControlPointNumber',
            'use only bounding box': 'm_bBoundBox',
            'cull outside instead of inside': 'm_bCullOutside',
            'hitbox set': 'm_HitboxSetName',
        }),
        'Cull relative to Ray Trace Environment': ('C_INIT_RtEnvCull', {
            'cull on miss': 'm_bCullOnMiss',
            'velocity test adjust lifespan': 'm_bLifeAdjust',
            'use velocity for test direction': 'm_bUseVelocity',
            'test direction': 'm_vecTestDir',
            'cull normal': 'm_vecTestNormal',
            'ray trace environment name': 'm_RtEnvName',
        }),
        'Normal Align to CP': ('C_INIT_NormalAlignToCP', {
            'control_point_number': 'm_nControlPointNumber',
        }),
        'Normal Modify Offset Random': ('C_INIT_NormalOffset', {
            'control_point_number': 'm_nControlPointNumber',
            'offset min': 'm_OffsetMin',
            'offset max': 'm_OffsetMax',
            'offset in local space 0/1': 'm_bLocalCoords',
            'normalize output 0/1': 'm_bNormalize',
        }),
        'Remap Speed to Scalar': ('C_INIT_RemapSpeedToScalar', {
            'emitter lifetime start time (seconds)': 'm_flStartTime',
            'emitter lifetime end time (seconds)': 'm_flEndTime',
            'control point number (ignored if per particle)': 'm_nControlPointNumber',
            'per particle': 'm_bPerParticle',
            'input minimum': 'm_flInputMin',
            'input maximum': 'm_flInputMax',
            'output field': 'm_nFieldOutput',
            'output minimum': 'm_flOutputMin',
            'output maximum': 'm_flOutputMax',
            'output is scalar of initial random range': BoolToSetKV(k='m_nSetMethod', v='PARTICLE_SET_SCALE_CURRENT_VALUE'),
        }),
        'Init From CP Snapshot': ('C_INIT_InitFromCPSnapshot', {
            'snapshot control point number': 'm_nControlPointNumber',
            'field to write': 'm_nAttributeToWrite',
            'field to read': 'm_nAttributeToRead',
            'local space control point number': 'm_nLocalSpaceCP',
        }),
        'Init From Killed Parent Particle': ('C_INIT_InitFromParentKilled', {
            'field to init': 'm_nAttributeToCopy',
        }),
        'Remap Initial Direction to CP to Vector': ('C_INIT_RemapInitialDirectionToCPToVector', {
            'control point': 'm_nCP',
            'output field': 'm_nFieldOutput',
            'normalize': 'm_bNormalize',
            'offset axis': 'm_vecOffsetAxis',
            'offset rotation': 'm_flOffsetRot',
            'scale factor': 'm_flScale',
        }),
        'Remap CP Orientation to Rotation': ('C_INIT_RemapInitialCPDirectionToRotation', {
            'control point': 'm_nCP',
            'rotation field': 'm_nFieldOutput',
            'axis': 'm_nComponent',
            'offset rotation': 'm_flOffsetRot',
        }),
        'Assign target CP': '',
        'Lifetime From Control Point Life Time': '',
        'Random position within a curved cylinder': '',
    }),

    'emitters': ('m_Emitters', {
        'emit_instantaneously': ('C_OP_InstantaneousEmitter', {
            'emission_start_time': 'm_flStartTime',
            'emission_start_time max': maxof('m_flStartTime'),  # m_flStartTimeMax
            'num_to_emit_minimum': minof('m_nParticlesToEmit'),  # m_nMinParticlesToEmit
            'num_to_emit': 'm_nParticlesToEmit',
            'maximum emission per frame': 'm_nMaxEmittedPerFrame',
            'emission count scale control point': 'm_nScaleControlPoint',
            'emission count scale control point field': 'm_nScaleControlPointField',
            'control point with snapshot data': 'm_nSnapshotControlPoint',
        }),
        'emit_continuously': ('C_OP_ContinuousEmitter', {
            'emission_start_time': 'm_flStartTime',
            'emission_rate': 'm_flEmitRate',
            'emission_duration': 'm_flEmissionDuration',
            'scale emission to used control points': 'm_flEmissionScale',
            'use parent particles for emission scaling': 'm_flScalePerParentParticle', #'m_bScalePerParticle',
            'emission count scale control point': 'm_nScaleControlPoint',
            'emission count scale control point field': 'm_nScaleControlPointField',
            'emit particles for killed parent particles': 'm_bInitFromKilledParentParticles',
        }),
        'emit noise': ('C_OP_NoiseEmitter', {
            'emission_start_time': 'm_flStartTime',
            'emission_duration': 'm_flEmissionDuration',
            'scale emission to used control points': 'm_flEmissionScale',
            'time noise coordinate scale': 'm_flNoiseScale',
            'time coordinate offset': 'm_flOffset',
            'absolute value': 'm_bAbsVal',
            'invert absolute value': 'm_bAbsValInv',
            'emission minimum': 'm_flOutputMin',
            'emission maximum': 'm_flOutputMax',
            'world time noise coordinate scale': 'm_flWorldTimeScale',
        }),
        'emit to maintain count': ('C_OP_MaintainEmitter', {
            'emission start time': 'm_flStartTime',
            'count to maintain': 'm_nParticlesToMaintain',
            'maintain count scale control point': 'm_nScaleControlPoint',
            'maintain count scale control point field': 'm_nScaleControlPointField',
            'control point with snapshot data': 'm_nSnapshotControlPoint',
        }),
    }),
    'forces': ('m_ForceGenerators', {
        'random force': ('C_OP_RandomForce', {
            'min force': 'm_MinForce',
            'max force': 'm_MaxForce',
        }),
        'Create vortices from parent particles': ('C_OP_ParentVortices', {
            'amount of force': 'm_flForceScale',
            'twist axis': 'm_vecTwistAxis',
            'flip twist axis with yaw': 'm_bFlipBasedOnYaw',
        }),
        'twist around axis': ('C_OP_TwistAroundAxis', {
            'amount of force': 'm_fForceAmount',
            'twist axis': 'm_TwistAxis',
            'object local space axis 0/1': 'm_bLocalSpace',
        }),
        'Pull towards control point': ('C_OP_AttractToControlPoint', {
            'amount of force': dynamicparam('m_fForceAmount'),
            'falloff power': 'm_fFalloffPower',
            'control point number': 'm_nControlPointNumber',
        }),
        'Force based on distance from plane': ('C_OP_ForceBasedOnDistanceToPlane', {
            'Min distance from plane': 'm_flMinDist',
            'Force at Min distance': 'm_vecForceAtMinDist',
            'Max Distance from plane': 'm_flMaxDist',
            'Force at Max distance': 'm_vecForceAtMaxDist',
            'Plane Normal': 'm_vecPlaneNormal',
            'Control point number': 'm_nControlPointNumber',
            'Exponent': 'm_flExponent',
        }),
        'lennard jones force': ('C_OP_LennardJonesForce', {
            'interaction radius': 'm_fInteractionRadius',
            'surface tension': 'm_fSurfaceTension',
            'lennard jones attractive force': 'm_fLennardJonesAttraction',
            'lennard jones repulsive force': 'm_fLennardJonesRepulsion',
            'max repulsion': 'm_fMaxRepulsion',
            'max attraction': 'm_fMaxAttraction',
        }),
        'time varying force': ('C_OP_TimeVaryingForce', {
            'time to start transition': 'm_flStartLerpTime',
            'starting force': 'm_StartingForce',
            'time to end transition': 'm_flEndLerpTime',
            'ending force': 'm_EndingForce',
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
        'up': NotImplemented,
        'down': NotImplemented,
   }),

    'constraints': ('m_Constraints', {
        'Constrain distance to control point': ('C_OP_ConstrainDistance', {
            'minimum distance': 'm_fMinDistance',
            'maximum distance': 'm_fMaxDistance',
            'control point number': 'm_nControlPointNumber',
            '': 'm_nScaleCP',
            'offset of center': 'm_CenterOffset',
            'global center point': 'm_bGlobalCenter',
        }),
        'Constrain distance to path between two control points': ('C_OP_ConstrainDistanceToPath', {
            'minimum distance': 'm_fMinDistance',
            'maximum distance': 'm_flMaxDistance0',
            'maximum distance middle': 'm_flMaxDistanceMid',
            'maximum distance end': 'm_flMaxDistance1',
            'travel time': 'm_flTravelTime',
            # m_PathParameters and not m_PathParams, for some reason
            'random bulge': ObjectP('m_PathParameters', 'm_flBulge'),
            'start control point number': ObjectP('m_PathParameters', 'm_nStartControlPointNumber'),
            'end control point number': ObjectP('m_PathParameters', 'm_nEndControlPointNumber'),
            'bulge control 0=random 1=orientation of start pnt 2=orientation of end point': ObjectP('m_PathParameters', 'm_nBulgeControl'),
            'mid point position': ObjectP('m_PathParameters', 'm_flMidPoint'),
        }),
        'Prevent passing through a plane': ('C_OP_PlanarConstraint', {
            'control point number': 'm_nControlPointNumber',
            'plane point': 'm_PointOnPlane',
            'plane normal': 'm_PlaneNormal',
            'global origin': 'm_bGlobalOrigin',
            'global normal': 'm_bGlobalNormal',
            # m_PointOnPlane m_PlaneNormal dynamicparam('m_flRadiusScale') dun(m_flMaximumDistanceToCP)
        }),
        'Prevent passing through static part of world': 'C_OP_WorldCollideConstraint',

        'Collision via traces': ('C_OP_WorldTraceConstraint', {
            'collision mode': remap('m_nCollisionMode', map = {
                0: 'COLLISION_MODE_PER_PARTICLE_TRACE',
                1: 'COLLISION_MODE_PER_FRAME_PLANESET',
                2: 'COLLISION_MODE_INITIAL_TRACE_DOWN',
                3: 'COLLISION_MODE_USE_NEAREST_TRACE',
            }),
            'amount of bounce': dynamicparam('m_flBounceAmount'),
            'amount of slide': dynamicparam('m_flSlideAmount'),
            'radius scale': 'm_flRadiusScale',
            'brush only': 'm_bBrushOnly',
            'collision group': 'm_CollisionGroupName',
            'control point offset for fast collisions': 'm_vecCpOffset',
            'control point movement distance tolerance': 'm_flCpMovementTolerance',
            'kill particle on collision': 'm_bKillonContact',
            'minimum speed to kill on collision': 'm_flMinSpeed',
            'Confirm Collision': 'm_bConfirmCollision',
            'trace accuracy tolerance': 'm_flTraceTolerance',
            'control point': 'm_nCP' # not in csgo src
        }),
        'Constrain particles to a box': ('C_OP_BoxConstraint', {
            'min coords': 'm_vecMin',
            'max coords': 'm_vecMax',
            #m_nCP = 4
			#m_bLocalSpace = true
        }),
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
    '__initializer_shared': {
        'run for killed parent particles': lambda v: None if not v else ('m_nMissingParentBehavior', "MISSING_PARENT_KILL"),#'m_bRunForParentApplyKillList', #
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
        'operator time strength random scale max': 'm_flOpStrengthMaxScale',
        'operator strength scale seed': 'm_nOpStrengthScaleSeed', # 

    },

    'children': ('m_Children', {
        'child': Ref('m_ChildRef'),
        'delay': 'm_flDelay',
        'end cap effect': 'm_bEndCap',

    }),
    'material': NotImplemented,#Ref('m_hMaterial'),

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
    'maximum portal recursion depth': 'm_nMaxRecursionDepth',
    'fallback_dx80': '',
    'draw through leafsystem': 'm_bDrawThroughLeafSystem',
    'preventNameBasedLookup': '',

}

for key, value in (alternate_names:= {
    'Color Light From Control Point': 'C_OP_ControlpointLight',
    'basic_movement': 'C_OP_BasicMovement',
    'radius_scale': 'C_OP_InterpolateRadius',
    'alpha_fade': 'C_OP_FadeAndKill', # C_OP_FadeOutSimple
    'color_fade': 'C_OP_ColorInterpolate',
    'rotation_spin': 'C_OP_Spin',
    'postion_lock_to_controlpoint': 'C_OP_PositionLock',
    'lifespan_decay': 'C_OP_Decay',
    'alpha_fade_in_random': 'C_OP_FadeIn',
    'alpha_fade_out_random': 'C_OP_FadeOut',
    'oscillate_vector': 'C_OP_OscillateVector',
    'oscillate_scalar': 'C_OP_OscillateScalar',
    'Dampen Movement Relative to Control Point': 'C_OP_DampenToCP',
    'rotation_spin yaw': 'C_OP_SpinYaw',
    'remap dot product to scalar': 'C_OP_RemapDotProductToScalar',
    'lock to bone': 'C_OP_LockToBone',
    'fade_and_kill': 'C_OP_FadeAndKill',
    'Random Cull': 'C_OP_Cull',
}).items():
    if not value:
        continue
    for pvalue in pcf_to_vpcf['operators'][1].copy().values():
        if pvalue[0] == value:
            pcf_to_vpcf['operators'][1].setdefault(key, (value, pvalue[1]))

for key, value in (alternate_names2:= {
    'move particles between 2 control points': 'C_INIT_MoveBetweenPoints',
    'lifetime_random': 'C_INIT_RandomLifeTime',
    'color_random': 'C_INIT_RandomColor',
    'rotation_random': 'C_INIT_RandomRotation',
    'random_rotation': 'C_INIT_RandomRotation',
    'alpha_random': 'C_INIT_RandomAlpha',
    'position_offset_random': 'C_INIT_PositionOffset',
    'sequence_random': 'C_INIT_RandomSequence',
    'radius_random': 'C_INIT_RandomRadius', # gotta love multiple names
    'random_radius': 'C_INIT_RandomRadius',
    'position_within_box': 'C_INIT_CreateWithinBox',
    'position_within_sphere': 'C_INIT_CreateWithinSphere',
    'Randomly Flip Yaw': 'C_INIT_RandomYawFlip', # are these the same?
    'Initial Velocity Noise': 'C_INIT_InitialVelocityNoise',
    'trail_length_random': 'C_INIT_RandomTrailLength',
    'lifetime from sequence': 'C_INIT_SequenceLifeTime',
    'initialize_within_sphere': 'C_INIT_CreateWithinSphere',
    'remap initial scalar': 'C_INIT_RemapScalar',
    'remap scalar to vector': 'C_INIT_RemapScalarToVector',
    'Initial Scalar Noise': 'C_INIT_CreationNoise',
    'random position on model': 'C_INIT_CreateOnModel',
    'Inherit Velocity': 'C_INIT_InheritVelocity',
    'Position In CP Hierarchy': '', # suspect C_INIT_CreateFromCPs maybe needs processing
    'sequential position along path': 'C_INIT_CreateSequentialPathV2', # V2
    'remap control point to Vector': 'C_INIT_RemapCPtoVector',
}).items():
    if not value:
        continue
    for pvalue in pcf_to_vpcf['initializers'][1].copy().values():
        if isinstance(pvalue, tuple):
            cls, sub = pvalue
        else:
            cls, sub = pvalue, {}
        if cls == value:
            pcf_to_vpcf['initializers'][1].setdefault(key, (value, sub))

NotYetFound = ''

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

def get_for_case_insensitive_key(oldkey, oldval, table):
    oldkey = oldkey.lower()
    for k, vpcf_k in table.items():
        k = k.lower()
        if k == oldkey:
            return vpcf_k, oldval
    return None

def guess_key_name(key, value):
    key_words = key.replace('_', ' ').split(' ')

    shorts = {'minimum':'min', 'maximum':'max', 'simulation':'sim', 'rotation':'rot', 'interpolation':'lerp'}
    typepreffix = {
        bool:'b', float:'fl', int:'n', Ref:'h'
    }

    guess = 'm_' + typepreffix.get(type(value), '')
    # TODO: list -> vec, ang, ''
    for kw in key_words[:3]:
        if kw.startswith('('):
            break
        elif '#' in kw or "'" in kw: break
        kw = shorts.get(kw, kw)
        guess += kw.capitalize()
    return guess, value

def guess_class_name(cls, _type):
    #cls = cls.replace('#', '').replace("'", '')
    key_words = cls.replace('_', ' ').split(' ')
    preffix = "OP"
    if _type == 'initializers':
        preffix = "INIT"
    guess = f"C_{preffix}_"
    for kw in key_words[:11]:
        guess += kw.capitalize()
    return guess

materials = set()
children = []
vsnaps = {}
fallbacks = []

def process_material(value):
    if not value:
        return

    vmt_path = Path(PATH_TO_CONTENT_ROOT) / value
    vmat_path = Path('materials') / Path(value).with_suffix('.vmat')
    vpcf._base_t['m_Renderers']['m_hMaterial'] = resource(vmat_path)
    try:
        vmt = VMT(KV.FromFile(vmt_path))
    except FileNotFoundError:
        materials.add(value)
    else:
        if (shader_add:=vmtshader.get(vmt.shader)) is not None:
            if not shader_add == '':
                if isinstance(shader_add, tuple):
                    vpcf._base_t['m_Renderers'][shader_add[0]] = shader_add[1]
                else:
                    vpcf._base_t['m_Renderers'][shader_add] = True
        else:
            un(vmt.shader, 'VMTSHADER')
        non_opaque_params = ('$addbasetexture2', '$dualsequence', '$sequence_blend_mode', '$maxlumframeblend1', '$maxlumframeblend2', '$extractgreenalpha', '$ramptexture', '$zoomanimateseq2', '$addoverblend', '$addself', '$blendframes', '$depthblend', '$inversedepthblend')
        if vmt.KeyValues.get('$opaque', 0) == 1:
            for nop in non_opaque_params:
                print('deleted', nop, vmt.KeyValues[nop])
                del vmt.KeyValues[nop]
        if vmt.KeyValues.get('$addself') == 1 and vmt.KeyValues.get('$additive') is None: # fix this addself thing?
            vmt.KeyValues['$additive'] = 1
        for vmtkey, vmtval in vmt.KeyValues.items():
            if '?' in vmtkey: vmtkey = vmtkey.split('?')[1]
            if vmtkey in ('$basetexture', '$material', '$normalmap', '$bumpmap'):
                vtex_ref = resource((Path('materials') / vmtval).with_suffix('.vtex'))
                vpcf_replacement_key = 'm_hTexture' if vmtkey in ('$basetexture', '$material') else 'm_hNormalTexture'
                vpcf._base_t['m_Renderers'][vpcf_replacement_key] = vtex_ref
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
                vpcf._base_t['m_Renderers'][add] = vmtval
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
    if isinstance(vpcf_translation, str):  # simple translation
        if value == []:
            return
        if isinstance(vpcf_translation, Ref):
            if not value:
                return
            if key == 'snapshot':
                vsnaps[vpcf.localpath] = value
            return str(vpcf_translation), resource(Path(vpcf.localpath.parent / (value  + '.vpcf')))

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
            functionName = opitem.get('functionName', opitem.name)
            className = None
            sub_translation = vpcf_translation[1]
            if key != 'children':
                if (className := sub_translation.get(functionName)):
                    # handle the 2 formats
                    # {'oldclass': 'newclass', 'oldk':'newk'} <- this one has global subkeys
                    # {'oldclass': ('newclass', {'oldk':'newk'})}
                    if type(className) is tuple:
                        className, sub_translation = className

                if not className:
                    if className is None:
                        un(functionName, outKey)
                    className = guess_class_name(functionName, key)

                if className is NotImplemented:
                    continue
                
                subKV = { '_class': className, **vpcf._base_t.get(outKey, {})}

            else:
                subKV = {}

            for key2, value2 in opitem.items():
                if key2 == 'functionName':
                    #if value2 != opitem.name:
                    #    #print("functionName mismatch", value2, opitem.name)
                    #    functionName = value2
                    continue

                if not (subkey:=sub_translation.get(key2)):
                    #if key2 in pcf_to_vpcf['__operator_shared']:
                    subkey = pcf_to_vpcf['__operator_shared'].get(key2, subkey)
                    if key == 'renderers':
                        subkey = pcf_to_vpcf['__renderer_shared'].get(key2, subkey)
                    elif key == 'initializers':
                        subkey = pcf_to_vpcf['__initializer_shared'].get(key2, subkey)
                    
                    if not subkey:
                        if subkey is None:
                            un(key2, functionName)
                        elif isinstance(subkey, Discontinued):
                            # if subkey.at >= vpcf m_nBehaviorVersion: # TODO,, also maybe this is not here __bool__ -> True
                            #     continue
                            continue
                        elif (rv :=get_for_case_insensitive_key(key2, value, sub_translation)):
                            subkey, value = rv
                        else:
                            subkey, value = guess_key_name(key2, value2)

                if not key2 or not subkey:
                    continue

                if isinstance(subkey, ObjectP):
                    subKV.setdefault(subkey.mother, {})[subkey.name] = value2
                    continue
                if isinstance(subkey, Ref):
                    if isinstance(value2, dmx.Element):
                        value2 = value2.name
                    else: input(f'Ref not an element {key2}: {value2}')
                    value2 = resource(Path(vpcf.localpath.parent / (value2  + '.vpcf')))
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

        if outVal != []:
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
            if any(isinstance(item, dict) for item in obj):  # TODO: only non numbers
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
            # round off inaccurate dmx floats TODO: does this make any diff
            if type(obj) == float:
                obj = round(obj, 6)
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

def ImportParticleSnapshotFile():
    # in VRperf (yes) its dmx text
    # either way open and save as text dmx with ext .vsnap on content
    ...


class VPCF(dict):
    header = '<!-- kv3 encoding:text:version{e21c7f3c-8a33-41c5-9977-a76d3a32aa0d} format:vpcf26:version{26288658-411e-4f14-b698-2e1e5d00dec6} -->'
    def __init__(self, **kwargs):
        self['_class'] = 'CParticleSystemDefinition'
        self.update(kwargs)

        self._base_t = dict(
            m_Renderers = dict(
                m_bFogParticles = True
            )
        )
    def text(self):
        return dict_to_kv3_text(self, self.header)

vpcf = None

def _import_ParticleSystemDefinition(ParticleSystemDefinition: dmx.Element, pack_root: Path) -> VPCF:
    global vpcf
    vpcf = VPCF( m_nBehaviorVersion = BEHAVIOR_VERSION )
    vpcf.localpath = pack_root / (ParticleSystemDefinition.name + '.vpcf')
    vpcf.path = particles_out.parent / vpcf.localpath
    imports.append(vpcf.localpath.as_posix())

    process_material(ParticleSystemDefinition.get('material'))

    for key, value in ParticleSystemDefinition.items():
        if converted_kv:= pcfkv_convert(key, value):
            if not converted_kv[0]:
                print('~ Warning: empty on', key, value)
            vpcf[converted_kv[0]] = converted_kv[1]

    # fix preoperators
    for operator in vpcf.get('m_Operators', ()):
        if not operator.get('_class') in vpcf_PreEmisionOperators:
            continue
        vpcf['m_Operators'].remove(operator)
        vpcf.setdefault('m_PreEmissionOperators', list())
        vpcf['m_PreEmissionOperators'].append(operator)

    with open(vpcf.path, 'w') as fp:
        fp.write(vpcf.text())

    print("+ Saved", vpcf.localpath.as_posix())

    return vpcf

def ImportPCFtoVPCF(pcf_path: Path) -> 'set[Path]':
    "Import `.PCF` particle pack to multiple separated `.VPCF`(s)"

    pcf = dmx.load(pcf_path)

    if not is_valid_pcf(pcf):
        print("Invalid!!")
        print(pcf.elements[0].keys())
        print(pcf.elements[1].type)
        return

    pack_root = particles / pcf_path.relative_to(particles_in).parent / pcf_path.stem
    (particles_out.parent / pack_root).mkdir(parents = True, exist_ok=True)
    out = set()
    for ParticleSystemDefinition in pcf.find_elements(elemtype='DmeParticleSystemDefinition'):
        out.add(_import_ParticleSystemDefinition(ParticleSystemDefinition, pack_root).path)
    return out

if __name__ == '__main__':
    for pcf_path in particles_in.glob('**/*.pcf'):
        #print(f"Reading particles/{pcf_path.name}")
        #if 'portal' in str(pcf_path):
        #    continue
        ImportPCFtoVPCF(pcf_path)

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
        spaces = ' ' * 12
        if k.startswith('m_'):
            spaces = ' ' * 8
        for i, n in enumerate(v):
            #if i == 0: print(f"    '{n}': '',")
            #else:
            print(f"{spaces}'{n}': '',")
        print()

    for n in generics:
        print(f"'{n}': '',")
    for snap in vsnaps:
        print(f'{snap} `{vsnaps[snap]}`')
    for child in children:
        if str(child.as_posix()) not in imports:
            print(child, "was not imported...")
    for fb in fallbacks:
        print(fb)
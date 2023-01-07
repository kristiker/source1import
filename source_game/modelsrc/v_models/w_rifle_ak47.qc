$modelname "w_models\Weapons\w_rifle_ak47.mdl"
$cdmaterials models\v_models\Weapons\rifle
$upaxis y

$opaque

//$attachment muzzle_flash "ValveBiped.flash" 0 0 0 rotate -90 0 0
//$attachment flashlight "ValveBiped.flashlight" 0 0 0 rotate 0 0 0
//$attachment shell "ValveBiped.shell_eject" 0 0 0 rotate 0 0 0 RIGID

$pushd "dmx"

$body main w_rifle_ak47.dmx
$sequence idle w_rifle_ak47.dmx


$surfaceprop "weapon"

$physskin 2
$physmaxpenetration 1
$physreduce verts 14
$collisionmodel "w_ak47_phys.dmx" 
{
     // Mass in kilograms
     $Mass 10
	//$concave
}
$keyvalues
{
"prop_data"
{
"base" "Metal.Medium"
}
}


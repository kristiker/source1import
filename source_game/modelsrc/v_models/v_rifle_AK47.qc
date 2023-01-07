$modelname "v_models\v_rifle_ak47.mdl"

$cdmaterials models\v_models\Weapons\rifle

$model v_rifle_ak47 "dmx/rifle_ak47_ref.dmx"

$include "Bones_Scripts\definebones.qci"
$include "Bones_Scripts\bonemerge.qci"




//game told me to do this:
$bonemerge "ValveBiped.weapon_bone" 

$origin 3 5 64

$pushd "dmx/animation"

$ikchain lhand "ValveBiped.Bip01_L_Hand"
$ikchain rhand "ValveBiped.Bip01_R_Hand"

$attachment "fowardnode" "ValveBiped.weapon_bone" 0 0 0 RIGID

$weightlist VIEWARMS "Valvebiped.Bip01" 1.0
$weightlist Sniper_ARM "Valvebiped.Bip01" 1.0


$animation a_idle_1 "ak47_idle.dmx" loop
$animation look_mid  "ak47_look_poses.dmx" frames 0 0 subtract a_idle_1 0 
$animation look_down "ak47_look_poses.dmx" frames 1 1 subtract a_idle_1 0 
$animation look_up   "ak47_look_poses.dmx" frames 2 2 subtract a_idle_1 0 

$sequence look_poses {
	look_down look_mid look_up
	blend ver_aims -1 1
	delta   
}

$animation a_run "ak47_run.dmx" fps 38 loop

$sequence idle_raw "ak47_idle.dmx" 

$sequence idle {
a_run a_idle_1 a_run
blend move_x -1 1
blendcenter a_idle_1
addlayer look_poses 
ACT_VM_IDLE 1
}

//$sequence idle_layer "ak47_idle.dmx" addlayer look_poses subtract idle 0 delta ACT_VM_IDLE_LAYER 1

$sequence deploy "ak47_deploy.dmx" ACT_VM_DEPLOY 1
$sequence deploy_layer "ak47_deploy.dmx" ACT_VM_DEPLOY_LAYER 1 { event 5004 1 "AK47.Deploy" }

$sequence fire "ak47_fire.dmx"{
	ikrule lhand touch "ValveBiped.weapon_bone" usesource
	ikrule rhand touch "ValveBiped.weapon_bone" usesource
ACT_VM_PRIMARYATTACK 1
{ event AE_MUZZLEFLASH 0 "1" }
}
$sequence fire_layer "ak47_fire.dmx" {
	ikrule lhand touch "ValveBiped.weapon_bone" usesource
	ikrule rhand touch "ValveBiped.weapon_bone" usesource
ACT_VM_PRIMARYATTACK_LAYER 1
{ event AE_MUZZLEFLASH 0 "1" }
}



$sequence reload "ak47_reload.dmx" fps 42 {
	activity ACT_VM_RELOAD 1
	{ event 5004 21 "AK47.ClipOut" }
	{ event 5004 42 "AK47.ClipIn" }
	{ event 5004 49 "AK47.ClipLocked" }
	{ event 5004 69 "AK47.SlideBack" }
	{ event 5004 76 "AK47.SlideForward" }
}

$sequence reload_layer "ak47_reload.dmx" fps 42 {
	ACT_VM_RELOAD_LAYER 1
	{ event 5004 21 "AK47.ClipOut" }
	{ event 5004 42 "AK47.ClipIn" }
	{ event 5004 49 "AK47.ClipLocked" }
	{ event 5004 69 "AK47.SlideBack" }
	{ event 5004 76 "AK47.SlideForward" }
}



//$sequence reload_pump "reload.dmx" frames 30 60 ACT_VM_RELOAD_PUMP 1
//$sequence reload_pump_layer "reload.dmx" frames 30 60 subtract idle 0 delta ACT_VM_RELOAD_PUMP_LAYER 1

$sequence melee "ak47_melee.dmx" {
	ikrule lhand touch "ValveBiped.weapon_bone" usesource
	ikrule rhand touch "ValveBiped.weapon_bone" usesource
ACT_VM_MELEE 1
}
$sequence melee_layer "ak47_melee.dmx" {
	ikrule lhand touch "ValveBiped.weapon_bone" usesource
	ikrule rhand touch "ValveBiped.weapon_bone" usesource
	subtract a_idle_1 0 delta 
ACT_VM_MELEE_LAYER 1
}

$sequence helping_hand_extend "ak47_helpinghand_extend.dmx" ACT_VM_HELPINGHAND_EXTEND 1
$sequence helping_hand_extend_layer "ak47_helpinghand_extend.dmx" fadeout 0.0 ACT_VM_HELPINGHAND_EXTEND_LAYER 1 	{ event 5004 1 "AK47.HelpingHandExtend" }

$sequence helping_hand_loop "ak47_helpinghand_loop.dmx" loop ACT_VM_HELPINGHAND_LOOP 1
$sequence helping_hand_loop_layer "ak47_helpinghand_loop.dmx" loop ACT_VM_HELPINGHAND_LOOP_LAYER 1

$sequence helping_hand_retract "ak47_helpinghand_retract.dmx" ACT_VM_HELPINGHAND_RETRACT 1
$sequence helping_hand_retract_layer "ak47_helpinghand_retract.dmx" fadein 0.0 ACT_VM_HELPINGHAND_RETRACT_LAYER 1 { event 5004 1 "AK47.HelpingHandRetract" }

$sequence item_extend "ak47_itempickup_extend.dmx" ACT_VM_ITEMPICKUP_EXTEND 1
$sequence item_extend_layer "ak47_itempickup_extend.dmx" fadeout 0.0 ACT_VM_ITEMPICKUP_EXTEND_LAYER 1 { event 5004 1 "AK47.ItemPickupExtend" }

$sequence item_loop "ak47_itempickup_loop.dmx" loop ACT_VM_ITEMPICKUP_LOOP 1
$sequence item_loop_layer "ak47_itempickup_loop.dmx" loop ACT_VM_ITEMPICKUP_LOOP_LAYER 1

$sequence item_retract "ak47_itempickup_retract.dmx" ACT_VM_ITEMPICKUP_RETRACT 1
$sequence item_retract_layer "ak47_itempickup_retract.dmx" fadein 0.0 ACT_VM_ITEMPICKUP_RETRACT_LAYER 1 { event 5004 1 "AK47.ItemPickupRetract" }






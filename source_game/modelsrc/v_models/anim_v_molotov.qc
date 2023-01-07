$modelname "v_models/anim_v_molotov.mdl"

$include "QCIs\definebones.qci"
$include "QCIs\bonemerge.qci"
$animblocksize 32

$ikchain rhand "valvebiped.Bip01_R_Hand" Z 0 knee 0.707 0.707 0

// Model (+)Right -- (-)Left		(+)Forward -- (-)Backward		(+)Down -- (-)Up
$origin		1.0								3.5						65.0
//$origin		0.0									0.0						65.0

$pushd "DMX/animation"


$weightlist VIEWARMS "Valvebiped.Bip01" 1.0


// -------------- IDLE ------------------------
$animation a_molotov_pose_neutral "v_eq_molotov_NamVet_Pose" frames 0 0
$animation a_molotov_arms_trans_down "v_eq_molotov_NamVet_Pose" frame 2 2 subtract a_molotov_pose_neutral 0 weightlist VIEWARMS
$animation a_molotov_arms_trans "v_eq_molotov_NamVet_Pose" frame 0 0 subtract a_molotov_pose_neutral 0 weightlist VIEWARMS
$animation a_molotov_arms_trans_up "v_eq_molotov_NamVet_Pose" frame 1 1 subtract a_molotov_pose_neutral 0 weightlist VIEWARMS
$sequence a_molotov_arms_vaims {
	a_molotov_arms_trans_down a_molotov_arms_trans a_molotov_arms_trans_up
	blend ver_aims  1 -1
	delta hidden
	}
$animation ta_molotov_run_trans_idle "v_eq_molotov_NamVet_Idle_02" ikrule rhand touch "ValveBiped.weapon_bone" 
$animation ta_molotov_run_trans_run "v_eq_molotov_NamVet_Run" ikrule rhand touch "ValveBiped.weapon_bone" 
$sequence molotov_idle {
	ta_molotov_run_trans_run ta_molotov_run_trans_idle ta_molotov_run_trans_run
	blend move_x 1 -1 loop
	addlayer a_molotov_arms_vaims
	activity ACT_VM_IDLE_MOLOTOV 1
   }

// ----------- DEPLOY -----------------------
$sequence molotov_deploy "v_eq_molotov_NamVet_Deploy" frame 0 40 FPS 50 snap activity ACT_VM_DEPLOY_MOLOTOV 1
	// ------layer-----
$animation molotov_anim_deploy_layer "v_eq_molotov_NamVet_Deploy" frame 0 40 FPS 50 subtract a_molotov_pose_neutral 0 weightlist VIEWARMS
$sequence molotov_deploy_layer {
	molotov_anim_deploy_layer weightlist VIEWARMS fadein 0 fadeout 0.6
	delta
	activity ACT_VM_DEPLOY_MOLOTOV_LAYER 1
}

	// ----------- PULLPIN -----------------------
$sequence molotov_pullpin "v_eq_molotov_NamVet_Pullback" frame 0 20 fps 40 snap activity ACT_VM_PULLPIN_MOLOTOV 1
$sequence molotov_pullpin_layer "v_eq_molotov_NamVet_Pullback" frame 0 20 fps 40 snap activity ACT_VM_PULLPIN_MOLOTOV_LAYER 1

	// ----------- THROW -----------------------
$sequence molotov_throw "v_eq_molotov_NamVet_Throw" frame 0 40 FPS 40 snap activity ACT_VM_THROW_MOLOTOV 1
	// ------layer-----
$sequence molotov_throw_layer {
	"v_eq_molotov_NamVet_Throw" frame 0 30 FPS 40  weightlist VIEWARMS snap
	activity ACT_VM_THROW_MOLOTOV_LAYER 1
}

// ----------- MELEE ATTACK -----------------------
$sequence molotov_melee "v_eq_molotov_NamVet_Melee" frame 0 40 fps 40 snap activity ACT_VM_MELEE_MOLOTOV 1
	// ------layer-----
$sequence molotov_melee_layer {
	"v_eq_molotov_NamVet_Melee" frame 0 40 FPS 40 weightlist VIEWARMS fadein 0.1 fadeout 0.4
	activity ACT_VM_MELEE_MOLOTOV_LAYER 1
}


 // ITEM PICKUP


// ----------- IDLE -----------------------
$sequence eq_molotov_ItemPickup_idle "v_eq_molotov_NamVet_ItemPickup" frame 30 90 snap loop FPS 30 activity ACT_VM_ITEMPICKUP_LOOP_MOLOTOV 1
	// ------layer-----
$sequence eq_molotov_ItemPickup_idle_layer {
	"v_eq_molotov_NamVet_ItemPickup" frame 30 90 loop snap FPS 30 fixuploop -3 3 weightlist VIEWARMS
	activity  ACT_VM_ITEMPICKUP_LOOP_MOLOTOV_LAYER 1
}

// ----------- EXTEND -----------------------
$sequence eq_molotov_ItemPickup_extend "v_eq_molotov_NamVet_ItemPickup" frame 0 30 snap FPS 80  activity  ACT_VM_ITEMPICKUP_EXTEND_MOLOTOV 1
	// ------layer-----
$sequence eq_molotov_ItemPickup_extend_layer {
	"v_eq_molotov_NamVet_ItemPickup" frame 0 50 snap FPS 80 weightlist VIEWARMS
	{ event 5004 1 "Molotov.ItemPickupExtend"  }
	activity ACT_VM_ITEMPICKUP_EXTEND_MOLOTOV_LAYER 1
}

// ----------- RETRACT -----------------------
$sequence eq_molotov_ItemPickup_retract "v_eq_molotov_NamVet_ItemPickup" frame 90 120 snap FPS 80  activity  ACT_VM_ITEMPICKUP_RETRACT_MOLOTOV 1
	// ------layer-----
$sequence eq_molotov_ItemPickup_retract_layer {
	"v_eq_molotov_NamVet_ItemPickup" frame 90 140 fadein 0.0 fadeout 0.3 FPS 80 weightlist VIEWARMS
	{ event 5004 1 "Molotov.ItemPickupRetract"  }
	activity ACT_VM_ITEMPICKUP_RETRACT_MOLOTOV_LAYER 1
}

 // HELPING HAND


// ----------- IDLE -----------------------
$sequence eq_molotov_HelpingHand_idle "v_eq_molotov_NamVet_HelpingHand" frame 30 90 snap loop FPS 30 activity ACT_VM_HELPINGHAND_LOOP_MOLOTOV 1
	// ------layer-----
$sequence eq_molotov_HelpingHand_idle_layer {
	"v_eq_molotov_NamVet_HelpingHand" frame 30 90 loop snap FPS 30 fixuploop -3 3 weightlist VIEWARMS
	activity  ACT_VM_HELPINGHAND_LOOP_MOLOTOV_LAYER 1
}

// ----------- EXTEND -----------------------
$sequence eq_molotov_HelpingHand_extend "v_eq_molotov_NamVet_HelpingHand" frame 0 30 snap FPS 80  activity  ACT_VM_HELPINGHAND_EXTEND_MOLOTOV 1
	// ------layer-----
$sequence eq_molotov_HelpingHand_extend_layer {
	"v_eq_molotov_NamVet_HelpingHand" frame 0 50 snap FPS 80 weightlist VIEWARMS
	{ event 5004 1 "Molotov.HelpingHandExtend"  }
	activity ACT_VM_HELPINGHAND_EXTEND_MOLOTOV_LAYER 1
}

// ----------- RETRACT -----------------------
$sequence eq_molotov_HelpingHand_retract "v_eq_molotov_NamVet_HelpingHand" frame 90 120 snap FPS 80  activity  ACT_VM_HELPINGHAND_RETRACT_MOLOTOV 1
	// ------layer-----
$sequence eq_molotov_HelpingHand_retract_layer {
	"v_eq_molotov_NamVet_HelpingHand" frame 90 140 fadein 0.0 fadeout 0.3 FPS 80 weightlist VIEWARMS
	{ event 5004 1 "Molotov.HelpingHandRetract"  }
	activity ACT_VM_HELPINGHAND_RETRACT_MOLOTOV_LAYER 1
}

$popd

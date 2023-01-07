$modelname "v_models\v_molotov.mdl"

$cdmaterials models\v_models\Weapons\eq_molotov

$include "QCIs/definebones.qci"
$include "QCIs/bonemerge.qci"

$ikchain rhand "valvebiped.Bip01_R_Hand" Z 0 knee 0.707 0.707 0

$opaque

$definebone "ValveBiped.jiggle_rag_dn0" "ValveBiped.weapon_bone" 0.000000 5.041567 0.000000 0.000000 0.000000 89.999983 0.000000 -0.000000 -0.000000 0.000000 0.000000 0.000000
$definebone "ValveBiped.jiggle_rag_dn1" "ValveBiped.jiggle_rag_dn0" 0.000000 -0.000000 2.529917 0.000000 0.000000 0.000000 0.000000 -0.000000 0.000000 0.000000 0.000000 0.000000
$definebone "ValveBiped.jiggle_rag_dn2" "ValveBiped.jiggle_rag_dn1" 0.000000 -0.000000 1.312244 0.000000 0.000000 0.000000 0.000000 -0.000000 0.000000 0.000000 0.000000 0.000000
$definebone "ValveBiped.jiggle_liquid" "ValveBiped.weapon_bone" 0.000000 2.095431 -0.000000 0.000000 0.000000 89.999983 0.000000 -0.000000 -0.000000 0.000000 0.000000 0.000000
$definebone "ValveBiped.jiggle_rag_up0" "ValveBiped.weapon_bone" 0.012893 8.012963 0.000000 -0.000000 145.475998 89.999983 -0.000000 -0.000000 0.000000 0.000000 -0.000000 0.000000
$definebone "ValveBiped.jiggle_rag_up1" "ValveBiped.jiggle_rag_up0" -0.256005 -0.000000 0.840425 -67.328484 180.000000 180.000007 -0.000000 -0.000000 -0.000000 -0.000000 0.000000 0.000000
$definebone "ValveBiped.jiggle_rag_up2" "ValveBiped.jiggle_rag_up1" 0.025142 -0.000000 2.053013 -25.126606 0.000000 0.000000 -0.000000 -0.000000 0.000000 -0.000000 0.000000 -0.000000
$definebone "ValveBiped.jiggle_rag_up3" "ValveBiped.jiggle_rag_up2" -0.009908 -0.000000 2.089445 8.892822 0.000000 -0.000000 -0.000000 -0.000000 -0.000000 -0.000000 0.000000 -0.000000


$jigglebone "ValveBiped.jiggle_rag_dn0" {
	is_flexible {
		yaw_stiffness 100
		yaw_damping 3
		pitch_stiffness 100
		pitch_damping 3
		angle_constraint 5
		length 15
	}
}

$jigglebone "ValveBiped.jiggle_rag_dn1" {
	is_flexible {
		yaw_stiffness 100
		yaw_damping 2
		pitch_stiffness 100
		pitch_damping 2
		angle_constraint 10
		length 15
	}
}

$jigglebone "ValveBiped.jiggle_rag_dn2" {
	is_flexible {
		yaw_stiffness 100
		yaw_damping 2
		pitch_stiffness 100
		pitch_damping 2
		angle_constraint 10
		length 15
	}
}

$jigglebone "ValveBiped.jiggle_rag_up0" {
	is_flexible {
		yaw_stiffness 900
		yaw_damping 10
		pitch_stiffness 900
		pitch_damping 10
		angle_constraint 10
		length 30
	}
}

$jigglebone "ValveBiped.jiggle_rag_up1" {
	is_flexible {
		yaw_stiffness 300
		yaw_damping 8
		pitch_stiffness 300
		pitch_damping 8
		angle_constraint 40
		length 15
	}
}

$jigglebone "ValveBiped.jiggle_rag_up2" {
	is_flexible {
		yaw_stiffness 100
		yaw_damping 6
		pitch_stiffness 100
		pitch_damping 6
		angle_constraint 80
		length 15
	}
}

$jigglebone "ValveBiped.jiggle_rag_up3" {
	is_flexible {
		yaw_stiffness 100
		yaw_damping 6
		pitch_stiffness 100
		pitch_damping 6
		angle_constraint 80
		length 15
	}
}


$jigglebone "ValveBiped.jiggle_liquid" {
	is_flexible {
		yaw_stiffness 50
		yaw_damping 1
		pitch_stiffness 50
		pitch_damping 1
		angle_constraint 30
		length 15
	}
}


$attachment "Wick" "valvebiped.Wick" 0 0 0 rotate 0 0 0 RIGID

$model molotov "DMX/v_eq_molotov_reference.smd"


// animation
$includemodel "v_models/anim_v_molotov.mdl"


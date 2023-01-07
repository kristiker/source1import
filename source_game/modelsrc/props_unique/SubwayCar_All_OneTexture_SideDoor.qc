$modelname props_unique\SubwayCar_All_OneTexture_SideDoor.mdl
$cdmaterials models\props_unique
 
$body "Body" "SubwayCar_All_OneTexture_SideDoor_REF.smd"  
$staticprop
$surfaceprop "metal"
// $illumposition 51 -80 90
 
// --------- Animation sequences ------- 
$sequence "idle" "SubwayCar_All_OneTexture_SideDoor_REF.smd" act_idle 1


$collisionmodel "SubwayCarExterior01_SideDoor01_PHY.smd" {
     // Mass in kilograms
     $Mass 30
  $concave
}

/*

$lod 25
{
replacemodel "SubwayCarExterior01_SideDoor01_REF.smd" "SubwayCarExterior01_SideDoor01_LOD_1.smd"
}

$lod 50
{
replacemodel "SubwayCarExterior01_SideDoor01_REF.smd" "SubwayCarExterior01_SideDoor01_LOD_2.smd"
}

$lod 75
{
replacemodel "SubwayCarExterior01_SideDoor01_REF.smd" "SubwayCarExterior01_SideDoor01_LOD_3.smd"
}

$lod 100
{
replacemodel "SubwayCarExterior01_SideDoor01_REF.smd" "SubwayCarExterior01_SideDoor01_LOD_4.smd"
}

$lod 150
{
replacemodel "SubwayCarExterior01_SideDoor01_REF.smd" "SubwayCarExterior01_SideDoor01_LOD_5.smd"
}

/*

$lod 48
{
replacemodel "SubwayCarExterior01_SideDoor01_REF.smd" "SubwayCarExterior01_SideDoor01_LOD_6.smd"
}


*/


$keyvalues
{
	"prop_data"
	{
		"base" "Metal.LargeHealth"
		"allowstatic" "1"
		"dmg.bullets" "0"
		"dmg.fire" "0"
		"dmg.club" ".35"
	//	"dmg.explosive" "1" 
		"multiplayer_break"	"both"
		"BlockLOS"	"1"
	}
}


$collisiontext
{
	"break"
	{
	"model" "props_unique\SubwayCarExterior01_SideDoor01_Damaged_01"
	"health" "10"
//	"fademindist" "10000"
//	"fademaxdist" "10000"
	}

	
	"break"
	{
	"model" "props_unique\SubwayCarExterior01_SideDoor01_Damaged_02"
	"health" "10"
//	"fadetime" "0"
//	"fademindist" "10000"
//	"fademaxdist" "10000"
	}

	"break"
	{
	"model" "props_unique\SubwayCarExterior01_SideDoor01_Damaged_03"
	"health" "10"
//	"fadetime" "0"
//	"fademindist" "10000"
//	"fademaxdist" "10000"
	}

"break"
	{
	"model" "props_unique\SubwayCarExterior01_SideDoor01_Damaged_04"
	"health" "10"
//	"fadetime" "0"
//	"fademindist" "10000"
//	"fademaxdist" "10000"
	}


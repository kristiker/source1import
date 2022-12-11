
echo hlvr
del /s /q "%cd%/source2_hlvr_game"
python ../utils/scripts_import.py -i "source_game" -e "%cd%/source2_hlvr_game"

echo sbox
del /s /q "%cd%/source2_sbox_game/"
python ../utils/scripts_import.py -i "source_game" -e "%cd%/source2_sbox_game"

rem echo dota2
rem del /s /q "%cd%/source2_adj_game"
rem python ../utils/scripts_import.py -i "source_game" -e "%cd%/source2_adj_game" --filter "propdata"


echo hlvr
rem del /s /q "%cd%/source2_hlvr_game"
python ../utils/scripts_import.py -i "source_game" -e "%cd%/source2_hlvr_game" ^
    --branch hlvr ^
    OVERWRITE_ASSETS=True ^

echo sbox
rem del /s /q "%cd%/source2_sbox_game/"
python ../utils/scripts_import.py -i "source_game" -e "%cd%/source2_sbox_game" ^
    --branch sbox ^
    OVERWRITE_ASSETS=True ^
    SOUNDSCAPES=True ^
    GAMESOUNDS=True ^
    SURFACES=True ^
    MISCELLANEOUS=False

echo adj
rem del /s /q "%cd%/source2_adj_game"
python ../utils/scripts_import.py -i "source_game" -e "%cd%/source2_adj_game" ^
    --branch adj ^
    OVERWRITE_ASSETS=True ^
    SOUNDSCAPES=False ^
    GAMESOUNDS=False ^
    SURFACES=False ^
    MISCELLANEOUS=True


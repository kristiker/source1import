import shared.datamodel as dmx
if __name__ is None:
    import utils.shared.datamodel as dmx

x = dmx.load(r'D:\Games\steamapps\common\Half-Life Alyx\content\csgo\particles\lighting.pcf')
for element in x.elements:
    with open(r'C:/Users/kristi/Desktop/lighting.txt', 'a') as fp:
        fp.write(f'{element.get_kv2()}\n')
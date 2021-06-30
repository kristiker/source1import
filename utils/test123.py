class VPCF(dict):
    def __init__(self, **kwargs):
        self['_class'] = "CParticleSystemDefinition"
        self.update(kwargs)


x = VPCF()

print(x)
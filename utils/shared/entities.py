from dataclasses import dataclass, field

@dataclass
class Entity:
    m_keyValuesData: bytearray
    m_connections: list

@dataclass
class Ents:
	m_name: str = "default_ents"
	m_hammerUniqueId: str = ""
	m_flags: str = "ENTITY_LUMP_NONE"
	m_manifestName: str = ""
	m_childLumps: list[str] = field(default_factory=list)
	m_entityKeyValues: list[Entity] = field(default_factory=list)

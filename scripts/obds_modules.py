"""
oBDS Module Reference

Official mapping of oBDS module numbers to their English names.

This reference file ensures consistent module naming across all analysis
scripts and visualizations.

Usage:
    from obds_modules import MODULE_NAMES, MODULE_NAMES_SHORT

Last updated: 2025-10-19
"""

# Full module names
MODULE_NAMES = {
    'Modul 5': 'Diagnosis',
    'Modul 6': 'Histology',
    'Modul 9': 'Other Classification',
    'Modul 10': 'Residual State',
    'Modul 11': 'Distant Metastasis',
    'Modul 12': 'General Health',
    'Modul 13': 'Surgery',
    'Modul 14': 'Radiation Therapy',
    'Modul 15': 'Adverse Events',
    'Modul 16': 'Systemic Therapy',
    'Modul 17': 'Progression',
    'Modul 18': 'Tumor Board',
    'Modul 19': 'Tumor Board',
    'Modul 20': 'Death',
    'Modul 21': 'Note',
    'Modul 22': 'Surgeon',
    'Modul 23': 'Genetic Variant',
    'Modul 24': 'Study',
    'Modul 25': 'Social Counseling',
}

# Short names with module prefix (for visualizations with limited space)
MODULE_NAMES_SHORT = {
    'Modul 5': 'M05: Diagnosis',
    'Modul 6': 'M06: Histology',
    'Modul 9': 'M09: Other Classification',
    'Modul 10': 'M10: Residual State',
    'Modul 11': 'M11: Distant Metastasis',
    'Modul 12': 'M12: General Health',
    'Modul 13': 'M13: Surgery',
    'Modul 14': 'M14: Radiation Therapy',
    'Modul 15': 'M15: Adverse Events',
    'Modul 16': 'M16: Systemic Therapy',
    'Modul 17': 'M17: Progression',
    'Modul 18': 'M18: Tumor Board',
    'Modul 19': 'M19: Tumor Board',
    'Modul 20': 'M20: Death',
    'Modul 21': 'M21: Note',
    'Modul 22': 'M22: Surgeon',
    'Modul 23': 'M23: Genetic Variant',
    'Modul 24': 'M24: Study',
    'Modul 25': 'M25: Social Counseling',
}

# Legacy modules (no longer in current structure)
LEGACY_MODULES = {}

# Notes
MODULE_NOTES = {
    'Modul 18': 'Combined with Module 19 as Tumor Board',
    'Modul 19': 'Combined with Module 18 as Tumor Board',
}


def get_module_name(module_key, short=False):
    """
    Get the English name for a module.

    Args:
        module_key (str): Module identifier (e.g., 'Modul 5')
        short (bool): If True, return short name with M## prefix

    Returns:
        str: Module name, or the original key if not found
    """
    mapping = MODULE_NAMES_SHORT if short else MODULE_NAMES

    if module_key in mapping:
        return mapping[module_key]
    elif module_key in LEGACY_MODULES:
        return LEGACY_MODULES[module_key]
    else:
        return module_key


def list_modules(include_legacy=False):
    """
    List all module numbers and names.

    Args:
        include_legacy (bool): Whether to include deprecated modules

    Returns:
        dict: Module mapping
    """
    if include_legacy:
        return {**MODULE_NAMES, **LEGACY_MODULES}
    else:
        return MODULE_NAMES.copy()

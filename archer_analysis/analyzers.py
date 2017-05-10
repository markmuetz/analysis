"""Provide an easy way of getting analyzer classes by name"""
from surf_flux_analysis import SurfFluxAnalyzer
from restart_dump_analysis import RestartDumpAnalyzer
from profile_analysis import ProfileAnalyzer

ANALYZERS = {
    'surf_flux_analysis': SurfFluxAnalyzer,
    'restart_dump_analysis': RestartDumpAnalyzer,
    'profile_analysis': ProfileAnalyzer,
}

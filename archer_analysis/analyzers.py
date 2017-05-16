"""Provide an easy way of getting analyzer classes by name"""
from surf_flux_analysis import SurfFluxAnalyzer
from restart_dump_analysis import RestartDumpAnalyzer
from profile_analysis import ProfileAnalyzer
from cloud_analysis import CloudAnalyzer
from mass_flux_analysis import MassFluxAnalyzer
from mass_flux_spatial_scales_analysis import MassFluxSpatialScalesAnalyzer

ANALYZERS = {
    SurfFluxAnalyzer.analysis_name: SurfFluxAnalyzer,
    RestartDumpAnalyzer.analysis_name: RestartDumpAnalyzer,
    ProfileAnalyzer.analysis_name: ProfileAnalyzer,
    CloudAnalyzer.analysis_name: CloudAnalyzer,
    MassFluxAnalyzer.analysis_name: MassFluxAnalyzer,
    MassFluxSpatialScalesAnalyzer.analysis_name: MassFluxSpatialScalesAnalyzer,
}

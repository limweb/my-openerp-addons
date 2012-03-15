"""
Aeroo Library
=============     
A templating library which provides a way to easily output ODF files (odt, ods).

Adding support for more filetype is easy:
you just have to create a plugin for this.

This reporting engine is based on work done by Relatorio project.

aeroolib also provides a report repository allowing you to link python objects
and report together, find reports by mimetypes/name/python objects.
"""
from reporting import MIMETemplateLoader, ReportRepository, Report
import plugins

__version__ = '1.0.0'

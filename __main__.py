# File: __main__.py
import pulumi

# Import modules for different resource groups
from infra import network
from infra import security
from infra import data 
from infra import compute
from infra import monitoring

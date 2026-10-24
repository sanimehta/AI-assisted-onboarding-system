import tempfile
from mcp.server.fastmcp import FastMCP
from onboard import generate

mcp = FastMCP('onboarding')

@mcp.tool()
def check_spec(spec: dict) -> dict:
    '''Validate an onboarding spec. An empty error list means the spec is valid.'''
    return {'errors': generate.validate_spec(spec, generate.load_used())}

@mcp.tool()
def suggest_chain(customer_name: str) -> dict:
    '''Suggest an unused 3 to 5 letter chain code for a customer name.'''
    return {'chain': generate.propose_chain(customer_name, generate.load_used())}

@mcp.tool()
def preview_project(spec: dict) -> dict:
    '''Build the project in a temporary folder and report errors and file names. Nothing is saved and no chain is reserved.'''
    with tempfile.TemporaryDirectory() as tmp:
        return generate.build_project(spec, generate.load_used(), out_root=tmp)

if __name__ == '__main__':
    mcp.run()
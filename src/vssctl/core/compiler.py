import subprocess
import shutil

from vssctl.core import paths


class Compiler:
    """
    Handles environment preparation and invoking the official VSS compiler.
    """

    def prepare_environment(self) -> None:
        """
        Creates workspace/generated/merged/ and copies all contents from team_vss/base/ to it.
        Then copies generated company.vspec into the merged directory.
        """
        # Clean or create merged directory
        if paths.MERGED_DIR.exists():
            shutil.rmtree(paths.MERGED_DIR)
        
        paths.MERGED_DIR.mkdir(parents=True, exist_ok=True)

        # Copy official VSS files
        if paths.TEAM_VSS_BASE.exists() and paths.TEAM_VSS_BASE.is_dir():
            for item in paths.TEAM_VSS_BASE.iterdir():
                if item.is_dir():
                    shutil.copytree(item, paths.MERGED_DIR / item.name)
                else:
                    shutil.copy2(item, paths.MERGED_DIR / item.name)

        # Copy generated company.vspec
        if paths.COMPANY_VSPEC.exists():
            shutil.copy2(paths.COMPANY_VSPEC, paths.MERGED_DIR / paths.COMPANY_VSPEC.name)

    def compile(self) -> None:
        """
        Invokes the official vspec2json compiler to generate the JSON.
        """
        merged_vehicle_vspec = paths.MERGED_DIR / "Vehicle.vspec"
        merged_company_vspec = paths.MERGED_DIR / "company.vspec"
        
        cmd = ["vspec2json"]

        # To merge cleanly, we specify Vehicle.vspec and then company.vspec
        # Assuming vspec2json supports multiple input files and the last is output
        # If standard Covesa tool is used, it takes an input and an output. 
        # Sometimes it requires the -I flag for includes.
        # We will pass both vspec files if they exist.
        cmd.append("-I")
        cmd.append(str(paths.MERGED_DIR))

        if merged_vehicle_vspec.exists():
            cmd.append(str(merged_vehicle_vspec))
            
        if merged_company_vspec.exists():
            cmd.append(str(merged_company_vspec))
        
        if not merged_vehicle_vspec.exists() and not merged_company_vspec.exists():
            raise RuntimeError("No .vspec files found to compile.")
            
        # Ensure output directory exists
        paths.METADATA_JSON.parent.mkdir(parents=True, exist_ok=True)
        
        cmd.append(str(paths.METADATA_JSON))

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"VSS compiler failed: {e.stderr}")

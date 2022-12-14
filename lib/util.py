import os

# Internal for calculation
_script_path = os.path.realpath( __file__ )
_script_directory = os.path.dirname( _script_path )
_parent_directory = os.path.dirname( _script_directory )

DB_DIR = os.path.join( _parent_directory, "db" )
POKEDEX_DIR = os.path.join( DB_DIR, "pokedex" )
ICON_DIR = os.path.join( DB_DIR, "icons" )
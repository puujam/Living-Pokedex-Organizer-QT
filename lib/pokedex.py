import json
import os
import importlib

from . import util

class Pokedex():
    """A Pokedex from a saved file"""

    def __init__( self, file_path ):
        self.load_data( file_path )
    
    def load_data( self, file_path ):
        with open( file_path, "r" ) as file_handle:
            self.data = json.load( file_handle )
    
    @property
    def pokemon( self ):
        return self.data[ "pokemon" ]

    @property
    def game( self ):
        return self.data[ "game" ]

    @property
    def region( self ):
        return self.data[ "region" ]
    
def create_all_pokedexes():
    results = list()
    
    for item in os.listdir( util.POKEDEX_DIR ):
        item_path = os.path.join( util.POKEDEX_DIR, item )
        if not os.path.isfile( item_path ):
            continue
        
        results.append( Pokedex( item_path ) )
        
    return results
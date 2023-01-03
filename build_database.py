import os
import json
import requests
from lib import util
from bs4 import BeautifulSoup

POKEMONDB_BASE_URL = "https://pokemondb.net"

def get_page( url ):
    print( "Downloading {}...".format( url ), end = "", flush = True )
    result = requests.get( url )
    print( "Done" )
    
    return result

def download_icon( pokemon_name, url ):
    file_path = os.path.join( util.ICON_DIR, "{}.png".format( pokemon_name.lower() ) )

    print( "Downloading icon for {}...".format( pokemon_name ), end = "", flush = True )
    
    image_data = requests.get( url ).content
    with open( file_path, "wb" ) as file_handle:
        file_handle.write( image_data )

    print( "Done" )

def dump_pokedex_file( game_name, region_name, pokemon ):
    sanitized_game_name = game_name.replace( "&", "and" ).replace( ":", "" )
    file_path = os.path.normpath( os.path.join( util.POKEDEX_DIR, "{}.json".format( sanitized_game_name ) ) )
    
    print( "Dumping to {}...".format( file_path ), end = "", flush = True )

    data = {
        "game": game_name,
        "region": region_name,
        "pokemon": pokemon
    }

    with open( file_path, "w" ) as file_handle:
        json.dump( data, file_handle )
    
    print( "Done" )

class PokemonDBRegionalDex:
    POKEMONDB_POKEDEX_URL = POKEMONDB_BASE_URL + "/pokedex"

    def __init__( self, game_name, region_name, suburl ):
        self.game_name = game_name.lower()
        self.region_name = region_name.lower()
        self.url = POKEMONDB_BASE_URL + suburl
    
        self.page = get_page( self.url )
        
        self.soup = BeautifulSoup( self.page.text, "html.parser" )
        
        self.parse_page()
    
    def parse_page( self ):
        self.pokemon = list()
        
        table_div = self.soup.find( class_ = "infocard-list infocard-list-pkmn-lg" )
        
        for div_tag in table_div.find_all( "div" ):
            text_span_tag = div_tag.find( class_ = "infocard-lg-data text-muted" )
            a_tag = text_span_tag.a
            
            pokemon_name = a_tag.text.lower()
            
            self.pokemon.append( pokemon_name )
    
    def dump_to_file( self ):
        dump_pokedex_file(self.game_name, self.region_name, self.pokemon)
    
class PokemonDBIconGrabber():
    """The "All" table from PokemonDB where we grab icons."""

    POKEMONDB_ALL_DEX_URL = POKEMONDB_BASE_URL + "/pokedex/all"
    
    def __init__( self ):
        self.page = get_page( PokemonDBIconGrabber.POKEMONDB_ALL_DEX_URL )
        
        self.soup = BeautifulSoup( self.page.text, "html.parser" )
    
    def dump_icons( self ):
        table = self.soup.find( name = "table", id = "pokedex" )
        
        table_body = table.tbody
        
        entries = table_body.find_all( "tr" )
        
        self.pokemon = set()
        for entry in entries:
            name_column = entry.find( class_ = "cell-name" )

            a_tag = name_column.a
            pokemon_name = a_tag.string
            
            # Only get the first image for a given pokemon
            if pokemon_name in self.pokemon:
                continue

            self.pokemon.add( pokemon_name )
            
            image_column = entry.find( class_ = "cell-num cell-fixed" )
            image_span = image_column.find( "span", class_ = "infocard-cell-img" )
            image_tag = image_span.img
            image_url = image_tag[ "src" ]
            download_icon( pokemon_name, image_url )

class PokemonDBNationalPokedex():
    POKEMONDB_NATIONAL_DEX_URL = POKEMONDB_BASE_URL + "/pokedex/national"

    def __init__( self ):
        self.page = get_page( PokemonDBNationalPokedex.POKEMONDB_NATIONAL_DEX_URL )
        
        self.soup = BeautifulSoup( self.page.text, "html.parser" )
        
        self.parse_page()
    
    def parse_page( self ):
        self.pokemon = list()
        
        for table_div in self.soup.find_all( class_ = "infocard-list infocard-list-pkmn-lg" ):
            for div_tag in table_div.find_all( "div" ):
                text_span_tag = div_tag.find( class_ = "infocard-lg-data text-muted" )
                a_tag = text_span_tag.a
                
                pokemon_name = a_tag.text.lower()
                
                self.pokemon.append( pokemon_name )

    def dump_to_file( self ):
        dump_pokedex_file( "national", "national", self.pokemon )

def create_regional_dexes():
    results = list()
    
    page = get_page( PokemonDBRegionalDex.POKEMONDB_POKEDEX_URL )
    soup = BeautifulSoup( page.text, "html.parser" )
    
    nav_tag = soup.find( "nav", class_ = "panel panel-nav" )
    ul_tag = nav_tag.find( "ul", class_ = None )
    
    for li_tag in ul_tag.find_all( "li" ):
        a_tag = li_tag.a
        game_name = a_tag.text

        suburl = a_tag[ "href" ]
        
        small_tag = li_tag.small
        region_name = small_tag.text.strip( "()" )

        if game_name == "National Dex":
            # We get the national dex separately
            continue

        results.append( PokemonDBRegionalDex( game_name, region_name, suburl ) )        
    
    return results

def create_dlc_dexes():
    results = list()

    # These aren't new regions, they've got slightly weird URL formats but I want them represented
    results.append( PokemonDBRegionalDex( "Sword & Shield - Isle of Armor", "Galar: Isle of Armor", "/pokedex/game/sword-shield/isle-of-armor" ) )
    results.append( PokemonDBRegionalDex( "Sword & Shield - Crown Tundra", "Galar: Crown Tundra", "/pokedex/game/sword-shield/crown-tundra" ) )
    
    return results

def main():
    regional_dexes = create_regional_dexes()
    regional_dexes.extend( create_dlc_dexes() )

    for regional_dex in regional_dexes:
        regional_dex.dump_to_file()

    national_dex = PokemonDBNationalPokedex()
    national_dex.dump_to_file()
    
    grabber = PokemonDBIconGrabber()
    grabber.dump_icons()

if __name__ == "__main__":
    main()
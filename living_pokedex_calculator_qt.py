import os
import sys
from lib import util
from lib import pokedex as pokedex_lib
from PySide6 import QtCore, QtWidgets, QtGui
from thefuzz import process as thefuzz_process


def calculate_box_and_coordinates( pokedex_number ):
    zero_indexed_pokedex_number = pokedex_number - 1

    zero_indexed_box = zero_indexed_pokedex_number // 30
    zero_indexed_position_within_box = zero_indexed_pokedex_number % 30
    zero_indexed_row = zero_indexed_position_within_box // 6
    zero_indexed_column = zero_indexed_position_within_box % 6

    box = zero_indexed_box + 1
    row = zero_indexed_row + 1
    column = zero_indexed_column + 1

    return box, row, column

class NumberWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.entry_label = QtWidgets.QLabel( "Pokedex Number:", alignment=QtCore.Qt.AlignLeft )
        self.number_entry = QtWidgets.QLineEdit( alignment = QtCore.Qt.AlignLeft )
        self.entry_validator = QtGui.QIntValidator()
        self.entry_validator.setBottom( 0 )
        self.number_entry.setValidator( self.entry_validator )
        self.number_entry.returnPressed.connect( self.pokedex_number_submitted )

        self.entry_row_layout = QtWidgets.QHBoxLayout( self )
        self.entry_row_layout.addWidget( self.entry_label )
        self.entry_row_layout.addWidget( self.number_entry )

    @QtCore.Slot()
    def pokedex_number_submitted( self ):
        try:
            pokedex_number = int( self.number_entry.text() )
        except ValueError:
            pokedex_number = 0
        
        self.parentWidget().parentWidget().parentWidget().change_highlighted_position( pokedex_number )

class NameWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        
        self.label = QtWidgets.QLabel( "Pokemon Name:", alignment = QtCore.Qt.AlignLeft )
        self.name_entry = QtWidgets.QLineEdit()
        self.name_entry.returnPressed.connect( self.pokemon_name_submitted )
        
        self.entry_row_layout = QtWidgets.QHBoxLayout( self )
        self.entry_row_layout.addWidget( self.label )
        self.entry_row_layout.addWidget( self.name_entry )
    
    @QtCore.Slot()
    def pokemon_name_submitted( self ):
        self.parentWidget().parentWidget().parentWidget().change_highlighted_pokemon( self.name_entry.text() )

class MyWidget(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.setStyleSheet("""
        QPushButton {
            background-color: white;
            border-style: outset;
            border-radius: 10px;
            padding: 6px;
        }
        """)
        
        self.selected_pokedex = None
        
        self.pokedexes = pokedex_lib.create_all_pokedexes()

        self.overall_layout = QtWidgets.QVBoxLayout( self )
        
        self.pokedex_dropdown = QtWidgets.QComboBox()
        self.populate_pokedex_dropdown()
        self.pokedex_dropdown.currentIndexChanged.connect( self.selected_pokedex_changed )

        self.tab_widget = QtWidgets.QTabWidget()
        self.number_widget = NumberWidget()
        self.tab_widget.addTab( self.number_widget, "Number" )
        self.name_widget = NameWidget()
        self.tab_widget.addTab( self.name_widget, "Name" )


        self.calculated_result = QtWidgets.QLabel( alignment = QtCore.Qt.AlignCenter )

        self.overall_layout.addWidget( self.pokedex_dropdown )
        self.overall_layout.addWidget( self.tab_widget )
        self.overall_layout.addWidget( self.calculated_result )
        
        self.buttons_layout = self.create_buttons_layout()
        self.overall_layout.addLayout( self.buttons_layout )
        
        # cleanup
        self.selected_pokedex_changed()
        
    def populate_pokedex_dropdown( self ):
        for index in range( len( self.pokedexes ) ):
            pokedex = self.pokedexes[ index ]
            item_name = "{} ({})".format( pokedex.game.title(), pokedex.region.title() )
            self.pokedex_dropdown.addItem( item_name, index )
    
    def create_buttons_layout( self ):
        self.buttons = list()

        buttons_veritcal_grid = QtWidgets.QVBoxLayout()
        
        self.visible_box_label = QtWidgets.QLabel( alignment = QtCore.Qt.AlignCenter )
        buttons_veritcal_grid.addWidget( self.visible_box_label )

        for row_index in range(5):
            column_layout = QtWidgets.QHBoxLayout()
            self.buttons.append( list() )

            for column_index in range(6):
                button = QtWidgets.QPushButton()
                button.setFixedSize( 80, 80 )
                button.setIconSize( QtCore.QSize( 75, 75 ) )
                
                button.row = row_index
                button.column = column_index
                button.clicked.connect( self.pokemon_clicked )

                column_layout.addWidget( button )
                self.buttons[row_index].append( button )
            
            buttons_veritcal_grid.addLayout( column_layout )
        
        scroll_button_layout = QtWidgets.QHBoxLayout()

        self.left_button = QtWidgets.QPushButton( "<" )
        self.left_button.clicked.connect( self.move_box_left )
        scroll_button_layout.addWidget( self.left_button )

        self.right_button = QtWidgets.QPushButton( ">" )
        self.right_button.clicked.connect( self.move_box_right )
        scroll_button_layout.addWidget( self.right_button )
        
        buttons_veritcal_grid.addLayout( scroll_button_layout )
        
        return buttons_veritcal_grid
    
    @QtCore.Slot()
    def selected_pokedex_changed( self ):
        self.selected_pokedex = self.pokedexes[ self.pokedex_dropdown.currentData() ]
        self.change_highlighted_position( None )
        self.set_visible_box( 0 )
        
    @QtCore.Slot()
    def move_box_left( self ):
        if self.visible_box_index > 0:
            self.set_visible_box( self.visible_box_index - 1 )
    
    @QtCore.Slot()
    def move_box_right( self ):
        self.set_visible_box( self.visible_box_index + 1 )
    
    @QtCore.Slot()
    def pokemon_clicked( self ):
        button = self.sender()
        
        self.change_highlighted_position_by_location( self.visible_box_index, button.row, button.column )
    
    def change_highlighted_pokemon( self, search_term ):
        if not self.selected_pokedex:
            return

        pokemon_name, match_strength = thefuzz_process.extractOne( search_term, self.selected_pokedex.pokemon )
        pokedex_number = self.selected_pokedex.pokemon.index( pokemon_name ) + 1

        self.change_highlighted_position( pokedex_number )
        
    def change_highlighted_position_by_location( self, box_index, row_index, column_index ):
        pokedex_number = ( box_index * 30 ) + ( row_index * 6 ) + column_index + 1

        self.change_highlighted_position( pokedex_number )

    def change_highlighted_position( self, pokedex_number ):
        if not pokedex_number or pokedex_number <=0:
            self.highlighted_box = None
            self.highlighted_row = None
            self.highlighted_column = None
            self.highlighted_pokedex_number = None
        else:
            self.highlighted_pokedex_number = pokedex_number
            self.highlighted_box, self.highlighted_row, self.highlighted_column = calculate_box_and_coordinates( pokedex_number )
            
            self.set_visible_box( self.highlighted_box - 1 )
        
        self.update_calculated_result_label()
            
    def update_calculated_result_label( self ):
        if not self.highlighted_box or not self.highlighted_row or not self.highlighted_column:
            self.calculated_result.setText( "" )
        elif self.highlighted_box == 0 or self.highlighted_row == 0 or self.highlighted_column == 0:
            self.calculated_result.setText( "Invalid Pokedex Number Entered!" )
        else:
            self.calculated_result.setText( "{}: {} - Box {}, Row {}, Column {}".format( self.highlighted_pokedex_number, self.highlighted_pokemon_name(), self.highlighted_box, self.highlighted_row, self.highlighted_column ) )
            
    def highlighted_pokemon_name( self ):
        if not self.selected_pokedex or self.highlighted_pokedex_number > len( self.selected_pokedex.pokemon ):
            return "???"
        
        return self.selected_pokedex.pokemon[ self.highlighted_pokedex_number - 1 ].title()
    
    def set_visible_box( self, box_index ):
        if not self.selected_pokedex:
            return

        self.visible_box_index = box_index

        box_number = self.visible_box_index + 1
        self.visible_box_label.setText( "Box {}".format( box_number ) )
        
        # I'm using magic numbers fuck you
        box_starting_pokedex_number = self.visible_box_index * 30
        
        for row_index in range(5):
            row_staring_pokedex_number = box_starting_pokedex_number + ( 6 * row_index )
            for column_index in range(6):
                button_pokedex_number = row_staring_pokedex_number + column_index
                button = self.buttons[ row_index ][ column_index ]
                
                if button_pokedex_number < len( self.selected_pokedex.pokemon ):
                    pokemon_name = self.selected_pokedex.pokemon[ button_pokedex_number ]
                    
                    icon_path = os.path.join( util.ICON_DIR, "{}.png".format( pokemon_name.lower() ) )
                    
                    if not os.path.isfile( icon_path ):
                        button.setIcon( QtGui.QIcon() )
                    else:
                        button.setIcon( QtGui.QIcon( icon_path ) )
                    
                    button.setToolTip( pokemon_name )
                else:
                    button.setIcon( QtGui.QIcon() )
                    button.setToolTip( "???" )
                    
                row_number = row_index + 1
                column_number = column_index + 1
                if box_number == self.highlighted_box and row_number == self.highlighted_row and column_number == self.highlighted_column:
                    button.setStyleSheet( "QPushButton { background-color: yellow }" )
                else:
                    button.setStyleSheet( "QPushButton { background-color: white }" )

if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    widget = MyWidget()
    widget.show()

    sys.exit(app.exec())
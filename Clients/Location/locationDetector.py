import sys
import numpy as np
import cv2


class ObjectLocation:
    '''This object gives the location of an item expressed as
        the a rectangle defined by its center, width, and height'''
    
    def __init__( self, x, y, width, height ):
        # x - coordinate along horizontal axis ( increasing left to right )
        # y - coordinate along vertical axis ( increasing top to bottom )
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def print( self ):
        print( "Item at x = {}, y = {}, of size: {}x{}".format( self.x, self.y, self.width, self.height ) )


class Layout:

    def __init__( self, bitmap=None, width=0, height=0 ):

        self.width = width
        self.height = height

        if isinstance( bitmap, np.ndarray ):
            self.height = bitmap.shape[0]
            self.width = bitmap.shape[1]
            self.bitmap = bitmap.copy()
        else:
            self.bitmap = np.zeros( (self.height,self.width) )

    def loadLayoutFromFile( self, fileName ):
        
        self.bitmap = cv2.imread( fileName, -1)

    def __sub__( self, rightOp ):

        width = min( self.width, rightOp.width )
        height = max( self.height, rightOp.height )
        resultLayout = Layout( width=width, height=height )
        resultLayout.bitmap = np.subtract( self.bitmap, rightOp.bitmap )
        resultLayout.bitmap = np.clip( resultLayout.bitmap, a_min=0, a_max=255 )
        resultLayout.bitmap = cv2.GaussianBlur( resultLayout.bitmap, (5,5), cv2.BORDER_DEFAULT )
    
        resultLayout.filterLayout( threshold=150 )    

        return resultLayout

    def __eq__( self, rightOp ):

        width = min( self.width, rightOp.width )
        height = min( self.height, rightOp.height )
        rightOp.filterLayout()

        temp = self - rightOp

        return np.sum( temp.bitmap ) < 5000 

    def filterLayout( self, threshold=50 ):
        '''This will remove any noise from the layout bitmap,
            leaving only strong features. For now let's define
            a strong feature as having a pixel value of 255.
            This will definitely need to be refined once we allow
            removing items from the scene. That will give us values
            CLOSE to 255 in ABSOLUTE VALUE'''

        self.bitmap[ self.bitmap < threshold ] = 0
        self.bitmap[ self.bitmap >= threshold ] = 255
        

class LocationDetector:
    def __init__( self, layout=None, initialLayoutFileName=None ):
        DEFAULT_LAYOUT_FILE = 'inputs/defaulLayout.pgm'
        
        self.updatedLayout = None
        self.itemsCollection = set()
        
        if initialLayoutFileName:
            self.initialFile = initialLayoutFileName
        else:
            self.initialFile = DEFAULT_LAYOUT_FILE
            
        if layout:
            self.defaultLayout = layout
        else:
            # read a static file
            self.defaultLayout = Layout()
            self.defaultLayout.loadLayoutFromFile( self.initialFile )
            
        self.defaultLayout.filterLayout()

    def saveLayout( self, saveFileName=None ):
        '''Will save the last snapshot of the layout.
            It might be a good idea to also save a collection of
            the objects found so far so we can recover after restart'''
        
        if saveFileName:
            fileName = saveFileName
        else:
            fileName = self.initialFile

        if self.updatedLayout is None:
            self.updatedLayout = self.defaultLayout

        cv2.imwrite( fileName, self.updatedLayout.bitmap )

    def _findNewItem( self, diffLayout ):
        '''Alright, this can be super optimized. Once we find the first 255
            we can move along the neighbouring 255. But for now let's do
            it the brute force way'''

        nonzeros = np.nonzero( diffLayout.bitmap )
        top = np.amin( nonzeros[0] )
        bottom = np.amax( nonzeros[0] )
        left = np.amin( nonzeros[1] )
        right = np.amax( nonzeros[1])
        
        return ObjectLocation( x = ( left + right ) / 2,
                               y = ( top + bottom ) / 2,
                               width = right - left,
                               height = bottom - top )

    def loadNewLayout( self, newLayoutFileName ):
        ''' maybe also return the lcoation of the new object???'''
        newLayout = Layout()
        newLayout.loadLayoutFromFile( newLayoutFileName )
        newLayout.filterLayout()
        
        if not self.updatedLayout is None:
            diffLayout = self.updatedLayout - newLayout
        else:
            diffLayout = self.defaultLayout - newLayout

        self.updatedLayout = newLayout
        
        newItemLocation = self._findNewItem( diffLayout )
        if newItemLocation:
            self.itemsCollection.add( newItemLocation )

        '''
        # Debugging: enable this and set which element you
        # want to isolate in the layout. It helps to see when
        # the picture isn't what it seems.
        
        if len(self.itemsCollection)==5:
            self.updatedLayout = diffLayout
        '''

    def addNewLayout( self, newLayout ):
        newLayout.filterLayout()
        
        if not self.updatedLayout is None:
            diffLayout = self.updatedLayout - newLayout
        else:
            diffLayout = self.defaultLayout - newLayout

        self.updatedLayout = newLayout
        newItemLocation = self._findNewItem( diffLayout )
        if newItemLocation:
            self.itemsCollection.add( newItemLocation )

        return newItemLocation, True

    def printItems( self ):
        print( "Items detected:" )
        for item in self.itemsCollection:
            item.print()
        print( " -------End of list---------" )
        

if __name__ == '__main__':
    locator = LocationDetector( initialLayoutFileName = 'inputs/sampleCoins_0.pgm' )
    locator.printItems()
    locator.saveLayout( saveFileName = 'outputs/detectedCoins_0.pgm' )

    for i in range( 1, 6 ):
        print( "\nAdding another item\n" )
        locator.loadNewLayout( newLayoutFileName = 'inputs/sampleCoins_{}.pgm'.format( i ) )
        locator.printItems()
        locator.saveLayout( saveFileName = 'outputs/detectedCoins_{}.pgm'.format( i ) )

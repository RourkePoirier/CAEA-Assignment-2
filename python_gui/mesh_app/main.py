from gui.manager import GUIManager
from geometry.manager import GeometryManager

def main():

    # Initialise geometry manager
    geometry = GeometryManager()

    gui = GUIManager(geometry)
    gui.run()

    
if __name__ == "__main__":
    main()
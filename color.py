# 2018-2025 ElenaBerry
from colorama import Fore, Back, Style
# B stands for background
# S stands for strong

class Trace:
    reset = Style.RESET_ALL
    normal = Style.NORMAL
    generic = Fore.CYAN
    name = Fore.LIGHTYELLOW_EX
    message = Fore.LIGHTGREEN_EX
    type = Fore.LIGHTMAGENTA_EX
    alert = Fore.LIGHTRED_EX
    warn = Fore.LIGHTYELLOW_EX
    id = Fore.LIGHTCYAN_EX
    time = Fore.LIGHTGREEN_EX
    
    class Styles:
        reset = Style.RESET_ALL
        normal = Style.NORMAL
        bold = Style.BRIGHT
        dim = Style.DIM
        bright = bold
        # The following aren't in colorama.
        # As so, they aren't really used.
        # These are the Windows code, and
        # will thus not work on other systems
        italics = '\033[3m'
        underline = '\033[4m'
        inverse = '\033[7m'
        strike = '\033[9m'
    style = Styles()

    class Black:
        class B:
            s = Back.LIGHTBLACK_EX

            def __str__(self):
                return Back.BLACK
        b = B()
        s = Fore.LIGHTBLACK_EX  # technically gray

        def __str__(self):
            return Fore.BLACK
    black = Black()
            
    class Red:
        class B:
            s = Back.LIGHTRED_EX

            def __str__(self):
                return Back.RED
        b = B()
        s = Fore.LIGHTRED_EX

        def __str__(self):
            return Fore.RED
    red = Red()
            
    class Green:
        class B:
            s = Back.LIGHTGREEN_EX

            def __str__(self):
                return Back.GREEN
        b = B()
        s = Fore.LIGHTGREEN_EX

        def __str__(self):
            return Fore.GREEN
    green = Green()
            
    class Yellow:
        class B:
            s = Back.LIGHTYELLOW_EX

            def __str__(self):
                return Back.YELLOW
        b = B()
        s = Fore.LIGHTYELLOW_EX

        def __str__(self):
            return Fore.YELLOW
    yellow = Yellow()
            
    class Blue:
        class B:
            s = Back.LIGHTBLUE_EX

            def __str__(self):
                return Back.BLUE
        b = B()
        s = Fore.LIGHTBLUE_EX

        def __str__(self):
            return Fore.BLUE
    blue = Blue()
            
    class Magenta:
        class B:
            s = Back.LIGHTMAGENTA_EX

            def __str__(self):
                return Back.MAGENTA
        b = B()
        s = Fore.LIGHTMAGENTA_EX

        def __str__(self):
            return Fore.MAGENTA
    magenta = Magenta()
            
    class Cyan:
        class B:
            s = Back.LIGHTCYAN_EX

            def __str__(self):
                return Back.CYAN
        b = B()
        s = Fore.LIGHTCYAN_EX

        def __str__(self):
            return Fore.CYAN
    cyan = Cyan()
            
    class White:
        class B:
            s = Back.LIGHTWHITE_EX

            def __str__(self):
                return Back.WHITE
        b = B()
        s = Fore.LIGHTWHITE_EX

        def __str__(self):
            return Fore.WHITE
    white = White()

    # Tuple of all color objects implemented in this class. 40 objects in total.
    tracers = (style.reset, style.normal, style.bold, style.dim, style.italics,
               style.underline, style.inverse, style.strike,

               black, black.s, black.b, black.b.s,
               red, red.s, red.b, red.b.s,
               green, green.s, green.b, green.b.s,
               yellow, yellow.s, yellow.b, yellow.b.s,
               blue, blue.s, blue.b, blue.b.s,
               magenta, magenta.s, magenta.b, magenta.b.s,
               cyan, cyan.s, cyan.b, cyan.b.s,
               white, white.s, white.b, white.b.s)


trace = Trace
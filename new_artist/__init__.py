from new_artist.panel import Panel, GRAPH_LIBRARY
from new_artist.figure import Figure, matrix, as_rows, as_cols
from new_artist.color import Color
from new_artist.drawable import FloatingCanvas


__version__ = '8.0.0'



"""
TODO LIST
    Axis should not include borders?

    Improve and merge bars and bhist

    axis ticks_scale => scale

    Add Axis objects

    Nicer repr and strs

    Superhistogram (and bar)
      -- Should be technically easy to do, but
      -- should ve actually think about how coordinate are trasferred to pixels?

    X) Documentation


POTENTIAL IDEAS / THINKING POINTS

    make some way to allign margins
        -- no need now?

    make panel coords pre-computed, instead of properties
        -- how much we gain from this?
        -- axes are pre-computed now
        -- how about .move()? They would need to call recompute on canvas
          -- Would work better if (A) is implemented

    rename draw <--> render
        -- why?
        -- draw = draw on the canvas, render - finalize the ideas
        -- what about "draw new" vs "draw onto something"?

    think about default values for matrix figures
        -- should they be scaled by size?

    A) Make Figures include reference to Panels, not panels themselbes
        -- i.e. in additional to Figure.items, have lists for Figure._shifts_x, Figure_shifts_y
        -- so it is easier to copy Figure
        -- would be impossible to use .move
        -- make copying in some other way?
        -- would require to put 'move' argument to all Plot

    Remove Color from the font object?
       -- any real use for it? only complications
       -- something.font.col = col
       -- is it a good another example?
       -- more arguments to pass to draw_axis?
           -- now we have axis.color, .tick_font, .label_font; We well need .font, .axis_color, .label_color, tick.color
           -- no problems with losing color when crating Axis(font=30) etc

    Make canvas into drawable?
        -- Would be much easier now
        -- Allow to sum and div Canvases, as well as do matrix of canvases
        -- The only problem is complexity and cross-references
        -- Also would require to make all drawables into FloatingDrawables

    Should Graph even be Drawable?

    Different way to define "single x coords or single col" ? Use 'X' vs 'x', 'C' or 'col'
        -- Since we are already checking names, this can be maybe easier than the current system?

    Long term idea: Make draw into functions
        -- make most method into functions?
        -- line(Canvas, x, y) would draw a line onto canvas, line(Panel, x, y) would create an object?
        -- line(Canvas) would run define() and draw() without creating an object?

    Plots that are compitely out of the defined domain should not contribure to the Margins?
        -- probably too of an edge case
        -- But it can be done with bounded_min / bounded_max dunctions

    Move all coord transformation to the Panel side?
        -- Ok, it would help with theorerical radial plot...
        -- at least when drawing, i.e. data transformation
        -- Graphs is not supposed to know it min or max without Panel...

    Binned mappings
        -- we have some graphs, which use categorical or binned systems
        -- cagorical mappings are quite easy to implements. In fact, they should be already working
        -- Binned mappings are more problematic; it is not immediately clear how they can work in current system
            -- to_value() should return interval?
        -- what about combining bin-cat and normal mapping in the same Panel?
            -- turning axis into cat or bin is trivial

        -- Linear mapping approach:
            -- use histogram with borders
            -- set axis with the same borders, so it would look neet
            -- can plot something on top
        -- Bin mapping approach
            -- define mapping with borders
            -- use histogram without borders
            -- axis should be ready automaticaly
            -- axis would look bad
            -- no way to hadle run-away values
            -- cannot plot anythong on top: lines would be weird

        -- Linear mapping color with shades
           -- does not cover the whole mapping
           -- cannot control borders
           -- color axis works automatically

        -- Linear mappin with binned mapping
           -- looks as degined
           -- color axis require special code
           -- however, color axis is easier to implement as cat mapping, not binned one

        -- question: is it possible to make a binned mapping, so that histograms and color axis would be autonatically easy?



DONE
    C) replace DrawableCollection with just a Figure ?
        -- Remove some extra levels
        -- We dont have Panel without Captions, why should we have Figure without Captions?
        -- Figure class is not super short code
    E) Drop "unit". Use different mappings instead
        -- units are easy to use
        -- but the are weird an limited
        -- unit easier to lin to axes, not dimensions
    E) Make axis for better time representation, i.e 'Sep\n2001'
        -- Separate Normal Axis and Perpendicual one into different classes as well?
    N) Proper alignment for text?
        -- Use pillow capacities, dont invent own
    P) Remove "<" and ">" coords, we dont need them. Proceed them at legend.define
    J) tests/dimension still contains examples of bad labbeling
        -- intersection labels
        -- time axes
        -- probably fine at this point
    U) Better grid marks
       -- current axis ticks interact badly with grid Plot
       -- make .suggest_tiks return simler output? or a more final one?

    D) In Plot.__init__, dot use _space, declare it explicitly
       -- Then it would be harder to create Plots, separated from Panels
       -- but do we need them at all?
       -- only for testing
    B) Add Color Axes
    H) Remove the need to .origin_x and _y
        -- Plot's origin should always be at 0, 0
        -- Would clean up a lot of code
        -- Turn out to be not as simple as that, as fuctions asssume canvas space to be the same as coord space
        -- Can be fixed by modifying .make() ?

    A) DEBUG mode?
        -- something to send to the "draw" or "save" method
        -- verbose output, coloring borders,
        -- saving everything what is derawn even when failing

    B) Move set_corrds from the Plot object?
       -- thus simplifying the Plot object, and setting data more explicitly
       -- what about comples unpacking, such as reading "<v" coords?

    RoratableGraph
        Fix roration of bitmaps? Or remove them complitely?
        Body? Think change how rotation works? or is it fine?
        Allow for more rotation possiblities in Rotatable plot? So they can be rotated and so on

    Weird interaction between rotations and alignment
        -- alignment seems to be not working with rotation
        -- do we ever need rotations?
        -- should be fine

    B) change coordinate system?
        -- (Into what? I forgot about this idea)
        -- Maibe about changing how canvas.to_coords work? Use top-left

    B) Try actual axes
       -- Do an actual computation of size?
       -- better perpendicualr axes.
       -- Multiline axis could be made default?
       -- Move creating labels into "propose ticks"?
       -- with hashed get_size it could be possible
    S) Standarsize positions of the arguemnts
       -- X, Y, col in all canvas
"""
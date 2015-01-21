'''
simple_sp_driver.py

A driver implementing Braun-Willett flow routing and then a
(non-fastscape) stream power component.
This version runs the model to something approximating steady 
state, then perturbs the uplift rate to produce a propagating
wave, then stores the propagation as a gif.
DEJH, 09/15/14
'''

from landlab.components.flow_routing.route_flow_dn import FlowRouter
from landlab.components.stream_power.stream_power import StreamPowerEroder
from landlab.components.stream_power.fastscape_stream_power import SPEroder as Fsc
from landlab.plot.video_out import VideoPlotter
from landlab.plot import channel_profile as prf
from landlab.plot import imshow as llplot

import numpy
from landlab import RasterModelGrid
from landlab import ModelParameterDictionary
import pylab
import time
import copy

inputs = ModelParameterDictionary('./drive_sp_params.txt')
nrows = inputs.read_int('nrows')
ncols = inputs.read_int('ncols')
dx = inputs.read_float('dx')
dt = inputs.read_float('dt')
time_to_run = inputs.read_float('run_time')
#nt needs defining
uplift = inputs.read_float('uplift_rate')
init_elev = inputs.read_float('init_elev')

mg = RasterModelGrid(nrows, ncols, dx)

#create the fields in the grid
mg.create_node_array_zeros('topographic_elevation')
z = mg.create_node_array_zeros() + init_elev
mg['node'][ 'topographic_elevation'] = z + numpy.random.rand(len(z))/1000.

print( 'Running ...' )

#instantiate the components:
fr = FlowRouter(mg)
sp = StreamPowerEroder(mg, './drive_sp_params.txt')
fsp = Fsc(mg, './drive_sp_params.txt')

#load the Fastscape module too, to allow direct comparison
fsp = Fsc(mg, './drive_sp_params.txt')
vid = VideoPlotter(mg, data_centering='node', step=2.5)

try:
    mg = copy.deepcopy(mg_mature)
except NameError:
    #run to a steady state:
    #We're going to cheat by running Fastscape SP for the first part of the solution
    elapsed_time = 0. #total time in simulation
    while elapsed_time < time_to_run:
        print elapsed_time
        if elapsed_time+dt>time_to_run:
            print "Short step!"
            dt = time_to_run - elapsed_time
        mg = fr.route_flow(grid=mg)
        #print 'Area: ', numpy.max(mg.at_node['drainage_area'])
        mg = fsp.erode(mg)
        #mg,_,_ = sp.erode(mg, dt, node_drainage_areas='drainage_area', slopes_at_nodes='steepest_slope')
        #add uplift
        mg.at_node['topographic_elevation'][mg.core_nodes] += uplift*dt
        elapsed_time += dt

    mg_mature = copy.deepcopy(mg)

else:
    #reinstantiate the components with the new grid
    fr = FlowRouter(mg)
    sp = StreamPowerEroder(mg, './drive_sp_params.txt')
    fsp = Fsc(mg, './drive_sp_params.txt')

    #load the Fastscape module too, to allow direct comparison
    fsp = Fsc(mg, './drive_sp_params.txt')
    vid = VideoPlotter(mg, data_centering='node', step=2.5)

#perturb:
time_to_run = 50.
dt=0.5
elapsed_time = 0. #total time in simulation
while elapsed_time < time_to_run:
    print elapsed_time
    vid.add_frame(mg, 'topographic_elevation', elapsed_time)
    if elapsed_time+dt>time_to_run:
        print "Short step!"
        dt = time_to_run - elapsed_time
    mg = fr.route_flow(grid=mg)
    #print 'Area: ', numpy.max(mg.at_node['drainage_area'])
    mg = fsp.erode(mg)
    #mg,_,_ = sp.erode(mg, dt, node_drainage_areas='drainage_area', slopes_at_nodes='steepest_slope')

    #plot long profiles along channels
    if numpy.allclose(elapsed_time%1.,0.) or numpy.allclose(elapsed_time%1.,1.):
        pylab.figure("long_profiles")
        profile_IDs = prf.channel_nodes(mg, mg.at_node['steepest_slope'],
                        mg.at_node['drainage_area'], mg.at_node['upstream_ID_order'],
                        mg.at_node['flow_receiver'])
        dists_upstr = prf.get_distances_upstream(mg, len(mg.at_node['steepest_slope']),
                        profile_IDs, mg.at_node['links_to_flow_receiver'])
        prf.plot_profiles(dists_upstr, profile_IDs, mg.at_node['topographic_elevation'])

    #add uplift
    mg.at_node['topographic_elevation'][mg.core_nodes] += 5.*uplift*dt

    elapsed_time += dt

#Finalize and plot
elev = mg['node']['topographic_elevation']
elev_r = mg.node_vector_to_raster(elev)

vid.produce_video()

# Clear previous plots
pylab.figure("topo")
pylab.close()

# Plot topography
pylab.figure("topo")
#im = pylab.imshow(elev_r, cmap=pylab.cm.RdBu)  # display a colored image
im = llplot.imshow_node_grid(mg, elev)
#print elev_r
#pylab.colorbar(im)
#pylab.title('Topography')

pylab.figure("Xsec")
im = pylab.plot(dx*numpy.arange(nrows), elev_r[:,int(ncols//2)])  # display a colored image
pylab.title('Vertical cross section')

pylab.figure("Slope-Area")
im = pylab.loglog(mg.at_node['drainage_area'], mg.at_node['steepest_slope'],'.')
pylab.title('Slope-Area')

pylab.show()

print('Done.')

    

#!/usr/bin/env python
import sys
import os 
## 
## mpirun 
##       -np 1 Syrthes02/syrthes -d Syrthes02/tmp.data --name Syrthes02 : 
##       -np 1 python /home/jmake/z2014/Cplng/Mpi4python/All_Beta/Tests/Python/coupling_syrthes01.py --name SYRTHES_COUPLING
##
#==================================================================| Parse |===#
from optparse import OptionParser
usage = "\n\t!! >> python ./%prog [options] arg1 arg2!!\n"
parser = OptionParser(usage=usage)
parser.add_option("-n", "--name", type="string", nargs=1,
                  dest="app_name", default=(''), help="application name")

(options, args) = parser.parse_args()

if options.app_name=='':
  parser.print_help()
  print 
  sys.exit() 


#===================================================================| init |===#
PATH = os.getcwd()
ROOT = "/home/jmake/z2014/Cplng/Mpi4python/All_Beta/"
sys.path.append(ROOT+"/Wrappers/Python")


#=================================================================| Mpi4py |===#
from mpi4py import MPI 
world_comm = MPI.COMM_WORLD
world_rank = world_comm.Get_rank()
world_size = world_comm.Get_size()


#=================================================================| COMMs |===#
import Commdomm
import Loader_alya
import Read_file 

"""
|_cs_syr_coupling.cs_syr_coupling_all_init
  |_ _init_all_mpi_syr
"""
app_type = "ALYA_CFD"
app_name = options.app_name

CD = Commdomm.CommDom() 
CD.init() 
CD.set_app_type(app_type);
CD.set_app_name(app_name);
CD.set_world_comm(world_comm)


local_comm = MPI.COMM_NULL
local_comm = CD.set_mpi_comms()
local_rank = local_comm.Get_rank()
local_size = local_comm.Get_size()


#==================================================================| MESH |===#
n_vertices_j    = 0
vertex_coords_j = Commdomm.darray( n_vertices_j )

n_vertices    = 0
vertex_coords = []

n_elements = 0
vertex_num = [] 


Types     = ["COORDINATES", "ELEMENTS", "CHARACTERISTICS"]
basenamei = ROOT+"/Tools/Meshes/Nastals/mesh01_%s.alya"
#rank      = str( 0 ).zfill(3) 

DATA = {}
for typei in Types: 
  filename = basenamei%(typei) 

  P = Read_file.read_log_file()
  P.set_name(filename)
  P.run()
  n_cols = P.get_cols()
  n_rows = P.get_rows()

  Data = []
  for i in range(n_rows): 
    data = []
    for j in range(1,n_cols): data.append( P.get_data_ij(i, j) ) 
    Data.append( data ) 
  P.end()
  DATA[typei] = Data


Elements = DATA["ELEMENTS"]
n_elements = len(Elements) 

vertex_num = []
for element in Elements:
  for node in element: vertex_num.append(int(node)-0) 
  #vertex_num.append(-169)


Coords = DATA["COORDINATES"]
n_vertices = len(Coords) 

vertex_coords = []
for coord in Coords:
  for pt in coord: vertex_coords.append(pt)


#===============================================================| LOCATOR |===#
local_comm.Barrier()


commij = MPI.COMM_NULL  
namei  = "SYRTHES_COUPLING"
namej  = "Syrthes02"
if( (CD.__get_app_name__() == namei) and (CD.__get_friends__(namej) == 1) ):
  #==| get communicator |==#
  commij = CD.get_mpi_commij(namej)

  #==||==#
  send   = 'coupling:type:%s%s0' % ('b',' ')
  n_send = len(send)

  recv   = "----++++----++++----++++----++++"
  n_recv = len(recv)

  CD.__mpi_sendrecv_char__(send, n_send, recv, n_recv, local_comm, commij)
  print "\'%s\'<-\'%s\'" %(namei, recv) 


  #==| init locator |==#
  CD.locator_create2(local_comm, commij)

  #==| init meshes |==#
  n_vertices_i    = n_vertices
  vertex_coords_i = Commdomm.darray( len(vertex_coords) )
  for i in range( len(vertex_coords) ): vertex_coords_i[i] = vertex_coords[i]

  n_elements_i    = n_elements
  vertex_num_i    = Commdomm.iarray( len(vertex_num) )
  for i in range( len(vertex_num) ): vertex_num_i[i] = vertex_num[i]

  print "\t +\'%s\' 01<-----" % namei 

  print "|_n_elements, n_vertices:", n_elements, n_vertices

  CD.locator_set_mesh(n_vertices_i, n_elements_i, vertex_coords_i, vertex_num_i, 
                      n_vertices_j, vertex_coords_j)

  CD.save_dist_coords(local_rank)

  print "\t +\'%s\' 02<-----" % namei 


  #==||==#
  send = 'coupling:start' 
  n_send = len(send)

  recv   = "----++++----++++----++++----++++"
  n_recv = len(recv)

  CD.__mpi_sendrecv_char__(send, n_send, recv, n_recv, local_comm, commij)
  print "\'%s\'<-\'%s\'" %(namei, recv) 
  print "\t +\'%s\' 03<-----" % namei 


  #==||==#
  CD.__syr_cfd_coupling_face_vars__() 
  print "\t +\'%s\' 04<-----" % namei 

  #CD._send_nodal_var() 
  print "\t +\'%s\' 05<-----" % namei 


  #==||==#
  ##__syr_cfd_coupling_ensure_conservativity__
  #n_send = 1
  #n_recv = 0
  #send   = Commdomm.darray(n_send)
  #recv   = Commdomm.darray(n_recv)
  #
  #send[0] = 1.0
  #CD.__mpi_sendrecv_real__(send, n_send, recv, n_recv, local_comm, commij)
  #print "\t +\'%s\' 06<-----" % namei 


  #==||==#
  print "\t +\'%s\' 0X<-----" % namei 

  for i in range(20): 
    #==||==#
    #local_comm.Barrier()
    CD.__syr_cfd_coupling_face_vars__() 
    print "\t +\'%s\' 04<-----" % namei 

    CD._send_nodal_var() 
    print "\t +\'%s\' 05<-----" % namei 


    #==||==#
    ##__syr_cfd_coupling_ensure_conservativity__
    #n_send = 1
    #n_recv = 0
    #send   = Commdomm.darray(n_send)
    #recv   = Commdomm.darray(n_recv)
    #
    #send[0] = 1.0
    #CD.__mpi_sendrecv_real__(send, n_send, recv, n_recv, local_comm, commij)
    #print "\t +\'%s\' 06<-----" % namei 

  #==||==#
  print "\t +\'%s\' 0X<-----" % namei 



#=========================================================================||===# 
#=========================================================================||===# 


#====================================================================| End |===# 
local_comm.Barrier()
if(local_rank==0):print "OK!!\n"
#=========================================================================||===# 

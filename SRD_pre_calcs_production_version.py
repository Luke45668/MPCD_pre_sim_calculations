#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thus May 11 13:20:52 2023

This script will does all the pre calcs for the SRD fluid mappings and then produces the simulation run files for myriad. 


@author: lukedebono
"""
#%%
import os
import numpy as np

import matplotlib.pyplot as plt
import regex as re
import pandas as pd

plt.rcParams.update({
    "text.usetex": True,
    "font.family": "Helvetica"
})
from mpl_toolkits import mplot3d
from matplotlib.gridspec import GridSpec
#import seaborn as sns
import math as m
import scipy.stats
from datetime import datetime
from petersen_plotting import *

#######################################################################################################################################################################################################################################################################################################################################################################################################################################################################################
# Fixed Values for all simulations #####
#######################################################################################################################################################################################################################################################################################################################################################################################################################################################################################

equilibration_timesteps= 1000 # number of steps to do equilibration with 
VP_ave_freq =1000
chunk = 20
atol=0.01
rtol=0.00001
#swap_rate = np.array([3,7,15,30,60,300,600,900,1200])# values chosen from original mp paper
#alternate set of swap rates we can only run 9 as we have a limit of 9 sims per node
swap_rate = np.array([5,9,12,22,45,180,450,750,1050])
swap_number = np.array([1,10,100,1000])
dump_freq=1000 # if you change the timestep rememebr to chaneg this 
thermo_freq = 10000
no_timesteps=500000 # might be worth lowering this in future 
realisation_index_ =np.linspace(0, 10,11)
tolerance=0.001# for solution error used 0.001 for 0.005, 0.01 for 0.0005
number_of_test_points =25
Solvent_bead_SRD_box_density_cp_1 = np.array([(np.linspace(10,20,number_of_test_points))])
number_of_M_cp_1=Solvent_bead_SRD_box_density_cp_1.shape[1]
k_b= 1.380649e-23 #boltzmann in J K^-1

# determine side length of simulation box
r_particle =50e-6
i=2 # this index sets the domain size 
phi=[0.005,0.0005,0.00005]
N=2
Vol_box_at_specified_phi= N* (4/3)*np.pi*r_particle**3 /phi[i]
box_side_length=np.cbrt(Vol_box_at_specified_phi)

# determine minimum number of collision cells based on total box size 
number_boxes_var=100 
# for 0.0005 23 worked as min  
min_number_boxes_for_particle_size=[24,52,112] #0.005,0.0005,0.00005

# this makes the boxes less than 0.25 r particle 
number_boxes_vec=np.linspace(min_number_boxes_for_particle_size[i],(min_number_boxes_for_particle_size[i]-1)+number_boxes_var,number_boxes_var)
def collision_cell_bound_enforcer():
    collision_cell_size=box_side_length/number_boxes_vec
    collision_cell_boolean= collision_cell_size > (r_particle/2)
    if np.any(collision_cell_boolean)==True:
        print("not enough collision cells to resolve around the particle")
    else: 
        print("Resolution achieved")
 
number_of_lengthscales=200       
max_particle_count =[150000,1500000,15000000]
min_particle_count=500

# computational settings for each domain size
wall_time=['4:00:00','8:00:00','20:00:00']
ram_requirement=['4G','8G','16G']
tempdir_req='50G'

#%% N2 Calculations #####
#Physical data 
fluid_name='Nitrogen'
scaled_timestep=0.01
rho_s = 847 #kg/m^3
Temp_visc_multiplier=0.0000046059
T_K=72.2 *  Temp_visc_multiplier#+273.15 #Kelvin
# linear interpolation
# to determine true visc from NIST data
eta_s_1 = 0.00022081
rho_1=	843.96
eta_s_2 = 0.00023138
rho_2 = 850.73	
delta_rho=rho_2-rho_1 
delta_eta_s =eta_s_2 - eta_s_1 
grad_eta_s_rho_s = delta_eta_s/delta_rho
eta_s_NIST=0.00022081 + ((rho_s -rho_1)*grad_eta_s_rho_s) 
eta_s=eta_s_NIST*Temp_visc_multiplier #*1000 to convert kg to g
nu_s = (eta_s/rho_s) 
temp_energy_to_nu_s_ratio= (k_b*T_K )/(eta_s_NIST/rho_s)
box_size_vec = np.array([box_side_length/number_boxes_vec])
mass_fluid_particle_wrt_pf_cp_mthd_1=(rho_s * (box_size_vec**3))/Solvent_bead_SRD_box_density_cp_1.T

#Multipliers for scalings 
length_multiplier=np.repeat(np.array([np.logspace(-2.5,-1.5,number_of_lengthscales)]).T,number_boxes_var,axis=1)
mass_multiplier=10000000
# Tolerance for SRD MD ratio 
srd_ratio_tolerance=150

#%% Ar Calculations #####
#Physical data 
fluid_name='Ar'
scaled_timestep=0.1
number_of_lengthscales=200
rho_s = 1426.9#621 #kg/m^3
Temp_visc_multiplier=0.000099
T_K=86.5 * Temp_visc_multiplier#+273.15 #Kelvin
eta_s_NIST=0.00029800 #Pa s
eta_s=eta_s_NIST* Temp_visc_multiplier#*1000 #*1000 to convert kg to g
nu_s = eta_s/rho_s
temp_energy_to_nu_s_ratio= (k_b*T_K )/(eta_s_NIST/rho_s)
box_size_vec = np.array([box_side_length/number_boxes_vec])
mass_fluid_particle_wrt_pf_cp_mthd_1=(rho_s * (box_size_vec**3))/Solvent_bead_SRD_box_density_cp_1.T

#Multipliers for scalings 
length_multiplier=np.repeat(np.array([np.logspace(-3,-1.5,number_of_lengthscales)]).T,number_boxes_var,axis=1)
mass_multiplier=1000000

# Tolerance for SRD MD ratio 
srd_ratio_tolerance=150

#%% H20 Calculations #####
#Physical data 
tolerance=0.01
fluid_name='H20'
scaled_timestep=0.01
rho_s = 1005##kg/m^3
Temp_visc_multiplier=1.612e-6
T_K=300* Temp_visc_multiplier
eta_s_NIST=0.00085253
eta_s=eta_s_NIST * Temp_visc_multiplier
nu_s = eta_s/rho_s
temp_energy_to_nu_s_ratio= (k_b*T_K )/(eta_s_NIST/rho_s)
box_size_vec = np.array([box_side_length/number_boxes_vec])
mass_fluid_particle_wrt_pf_cp_mthd_1=(rho_s * (box_size_vec**3))/Solvent_bead_SRD_box_density_cp_1.T

#Multipliers for scalings 
length_multiplier=np.repeat(np.array([np.logspace(-1,0,number_of_lengthscales)]).T,number_boxes_var,axis=1)
mass_multiplier=100

# Tolerance for SRD MD ratio 
srd_ratio_tolerance=8
#%% Hexane Calculations #####
#Physical data 
tolerance=0.01
fluid_name='C6H14'
scaled_timestep=0.01
rho_s = 700  #kg/m^3
Temp_visc_multiplier=0.00003
T_K=311* Temp_visc_multiplier
eta_s_NIST= 0.00046729
eta_s=eta_s_NIST * Temp_visc_multiplier
nu_s = eta_s/rho_s
temp_energy_to_nu_s_ratio= (k_b*T_K )/(eta_s_NIST/rho_s)
box_size_vec = np.array([box_side_length/number_boxes_vec])
mass_fluid_particle_wrt_pf_cp_mthd_1=(rho_s * (box_size_vec**3))/Solvent_bead_SRD_box_density_cp_1.T

#Multipliers for scalings 
length_multiplier=np.repeat(np.array([np.logspace(-1.5,0,number_of_lengthscales)]).T,number_boxes_var,axis=1)
mass_multiplier=100

# Tolerance for SRD MD ratio 
srd_ratio_tolerance=60
#%% The stand alone SRD(-a) calculations 
#produce tuples 
sc_pos_soln=()
sc_neg_soln=()

mean_free_path_pf_SRD_particles_cp_mthd_1_neg=()
mean_free_path_to_box_ratio_neg=()
mean_free_path_pf_SRD_particles_cp_mthd_1_pos=()
mean_free_path_to_box_ratio_pos=()

Number_MD_steps_per_SRD_with_pf_cp_mthd_1_neg=()
Number_MD_steps_per_SRD_with_pf_cp_mthd_1_pos=()

number_SRD_particles_wrt_pf_cp_mthd_1_neg=()
number_SRD_particles_wrt_pf_cp_mthd_1_pos=()

comparison_neg=()
comparison_pos=()

SRD_timestep_cp_1_based_on_sphere_pf_neg_nd=()
SRD_MD_ratio_neg=()
SRD_step_neg_nd=()
SRD_timestep_cp_1_based_on_sphere_pf_pos_nd=()
SRD_step_pos_nd=()
SRD_MD_ratio_pos=()

SRD_box_size_wrt_solid_beads=()
SRD_box_size_wrt_solid_beads_check = ()

energy_parameter=()
timescale_parameter=()
temperature_parameter=()
scaled_dynamic_viscosity=()
scaled_nu_s=()
scaled_rho_s=()
box_side_length_scaled=()
box_size_vec_nd=()

lengthscale_parameter = length_multiplier*r_particle
box_side_length_scaled=(box_side_length/lengthscale_parameter)
box_size_to_lengthscale=box_size_vec/lengthscale_parameter
SRD_mass_scale_parameter = mass_multiplier* rho_s * (lengthscale_parameter**3)
r_particle_scaled = r_particle/lengthscale_parameter
box_size_vec = np.array([box_side_length/number_boxes_vec])
box_size_vec_nd=box_side_length_scaled/number_boxes_vec
SRD_box_size_wrt_solid_beads_check=box_size_vec

for z in range(0,number_of_lengthscales):
   

    import units_lj_scalings
    scalings_calculation= units_lj_scalings.units_lj_scalings_(SRD_mass_scale_parameter[z,0],lengthscale_parameter[z,0],k_b,rho_s,eta_s,T_K)

    energy_parameter=energy_parameter+ (scalings_calculation[0],)
    timescale_parameter=timescale_parameter+(scalings_calculation[1],)
    temperature_parameter= temperature_parameter+(scalings_calculation[2],)
    scaled_dynamic_viscosity=temperature_parameter+(scalings_calculation[3],)
    scaled_nu_s=scaled_nu_s+(scalings_calculation[4],)
    scaled_rho_s=scaled_rho_s+(scalings_calculation[5],)
    scaled_temp=T_K/temperature_parameter[z]


    # do theoretical calcs 
    import numpy as np
    from SRD_master import *

    SRD_box_size_wrt_solid_beads= SRD_box_size_wrt_solid_beads+ (box_size_vec_nd[z,:],)
    SRD_non_dimensional_master_data=SRD_MASTER_calc_(mass_fluid_particle_wrt_pf_cp_mthd_1,box_side_length,number_boxes_vec,scaled_timestep,rtol,nu_s,Solvent_bead_SRD_box_density_cp_1, box_size_vec,box_size_vec_nd,SRD_box_size_wrt_solid_beads_check,box_side_length_scaled[z,0],T_K,SRD_mass_scale_parameter[z,0],lengthscale_parameter[z,0],k_b,rho_s,eta_s)                            
    
    sc_pos_soln=sc_pos_soln+(SRD_non_dimensional_master_data[0],)
    sc_neg_soln=sc_neg_soln+(SRD_non_dimensional_master_data[1],)
    
    mean_free_path_pf_SRD_particles_cp_mthd_1_neg=  mean_free_path_pf_SRD_particles_cp_mthd_1_neg+(SRD_non_dimensional_master_data[2],)
    mean_free_path_to_box_ratio_neg=mean_free_path_to_box_ratio_neg+((mean_free_path_pf_SRD_particles_cp_mthd_1_neg[z]/SRD_box_size_wrt_solid_beads[z]),)
    mean_free_path_pf_SRD_particles_cp_mthd_1_pos=mean_free_path_pf_SRD_particles_cp_mthd_1_pos+(SRD_non_dimensional_master_data[3],)
    mean_free_path_to_box_ratio_pos=mean_free_path_to_box_ratio_pos+((mean_free_path_pf_SRD_particles_cp_mthd_1_pos[z]/SRD_box_size_wrt_solid_beads[z]),)

    Number_MD_steps_per_SRD_with_pf_cp_mthd_1_neg=Number_MD_steps_per_SRD_with_pf_cp_mthd_1_neg+(SRD_non_dimensional_master_data[4],)
    Number_MD_steps_per_SRD_with_pf_cp_mthd_1_pos=Number_MD_steps_per_SRD_with_pf_cp_mthd_1_pos+(SRD_non_dimensional_master_data[5],)

    number_SRD_particles_wrt_pf_cp_mthd_1_pos = number_SRD_particles_wrt_pf_cp_mthd_1_pos+(((np.array([(box_side_length_scaled[z,:]**3)/(SRD_box_size_wrt_solid_beads[z]**3)]))*(Solvent_bead_SRD_box_density_cp_1.T)),)
    number_SRD_particles_wrt_pf_cp_mthd_1_neg=number_SRD_particles_wrt_pf_cp_mthd_1_pos 

    comparison_neg=   comparison_neg+(SRD_non_dimensional_master_data[6],)
    comparison_pos=  comparison_pos+(SRD_non_dimensional_master_data[7],)

    SRD_timestep_cp_1_based_on_sphere_pf_neg_nd=SRD_timestep_cp_1_based_on_sphere_pf_neg_nd+(SRD_non_dimensional_master_data[8],)
    SRD_MD_ratio_neg=SRD_MD_ratio_neg + ((SRD_timestep_cp_1_based_on_sphere_pf_neg_nd[z]/scaled_timestep),)
    SRD_step_neg_nd=SRD_timestep_cp_1_based_on_sphere_pf_neg_nd
    SRD_timestep_cp_1_based_on_sphere_pf_pos_nd= SRD_timestep_cp_1_based_on_sphere_pf_pos_nd+(SRD_non_dimensional_master_data[9],)
    SRD_step_pos_nd=SRD_timestep_cp_1_based_on_sphere_pf_pos_nd
    SRD_MD_ratio_pos=SRD_MD_ratio_pos+ ((SRD_timestep_cp_1_based_on_sphere_pf_pos_nd[z]/scaled_timestep),)

# now apply constraints
from MPCD_constraints_on_solutions import MPCD_constraints 

count_passed_constraints_neg=[]
count_passed_constraints_pos=[]
locations_of_non_nan_neg=()
locations_of_non_nan_pos=()

for z in range(0,number_of_lengthscales):
    
    MPCD_constraints(no_timesteps,min_particle_count,sc_neg_soln[z],sc_pos_soln[z],srd_ratio_tolerance,max_particle_count[i],number_SRD_particles_wrt_pf_cp_mthd_1_pos[z],number_SRD_particles_wrt_pf_cp_mthd_1_neg[z],mean_free_path_pf_SRD_particles_cp_mthd_1_neg[z],mean_free_path_pf_SRD_particles_cp_mthd_1_pos[z],Number_MD_steps_per_SRD_with_pf_cp_mthd_1_pos[z],Number_MD_steps_per_SRD_with_pf_cp_mthd_1_neg[z],Solvent_bead_SRD_box_density_cp_1,tolerance,SRD_box_size_wrt_solid_beads[z],comparison_pos[z],comparison_neg[z])
    count_passed_constraints_neg.append(np.count_nonzero(~np.isnan(Number_MD_steps_per_SRD_with_pf_cp_mthd_1_neg[z]))) 
    count_passed_constraints_pos.append(np.count_nonzero(~np.isnan(Number_MD_steps_per_SRD_with_pf_cp_mthd_1_pos[z])) )
  
    locations_of_non_nan_neg= locations_of_non_nan_neg+(np.argwhere(~np.isnan(Number_MD_steps_per_SRD_with_pf_cp_mthd_1_neg[z])),)
    locations_of_non_nan_pos= locations_of_non_nan_pos+(np.argwhere(~np.isnan(Number_MD_steps_per_SRD_with_pf_cp_mthd_1_pos[z])),)

#plot the count of successful solutions vs the value of ell
plt.rcParams.update({
    "text.usetex": True,
    "font.family": "Helvetica"
})
fig=plt.figure(figsize=(10,6))
gs=GridSpec(nrows=1,ncols=1)
fig.suptitle(fluid_name+': Solution Count vs Length scale',size='large', wrap=True)

ax1= fig.add_subplot(gs[0]) 
for z in range(0,number_of_lengthscales):
    
    ax1.set_xscale('log')
    ax1.set_ylabel('$C_{p,s}$',rotation='horizontal')
    ax1.set_xlabel('$\ell$ [-]')
    ax1.plot(lengthscale_parameter[:,0],count_passed_constraints_neg[:])#, marker='o',s=5)
plt.show()

# Assessing the solutions 
# if there is too much data in this section just 

index_of_tuples_passed=np.argwhere(count_passed_constraints_neg)

num_passed_solutions_in_each_tuple=[]
for z in range(0,index_of_tuples_passed.size):
          num_passed_solutions_in_each_tuple.append(count_passed_constraints_neg[index_of_tuples_passed[z][0]])
   
# need to create an array for each solution hat stores the data for multiple lnegth scales
# then concantenates that to another tuple

solution_data_tuple=()
for z in range(0,index_of_tuples_passed.size):
    solution_data_tuple=solution_data_tuple+(np.zeros((num_passed_solutions_in_each_tuple[z],2)),)
    for n in range(0,num_passed_solutions_in_each_tuple[z]):
        solution_row=locations_of_non_nan_neg[index_of_tuples_passed[z][0]][n][0]
        solution_col=locations_of_non_nan_neg[index_of_tuples_passed[z][0]][n][1]
        # MFP data col 0
        #solution_data_tuple[z][n,0]=mean_free_path_pf_SRD_particles_cp_mthd_1_neg[index_of_tuples_passed[z][0]][solution_row,solution_col]
        # SRD MD ratio data col 1
        solution_data_tuple[z][n,0]=Number_MD_steps_per_SRD_with_pf_cp_mthd_1_neg[index_of_tuples_passed[z][0]][solution_row,solution_col]
        # number data col 2
        solution_data_tuple[z][n,1]=number_SRD_particles_wrt_pf_cp_mthd_1_neg[index_of_tuples_passed[z][0]][solution_row,solution_col]
        

# now do plot of all solution points for each lengthscale, this allows us to tell which one has the least
# particles and the highest value of SRD/MD ratio
import sigfig
fontsize=12

for z in range(0,index_of_tuples_passed.size):
   # for n in range(0,num_passed_solutions_in_each_tuple[z]):
        
        plt.scatter( solution_data_tuple[z][:,1],solution_data_tuple[z][:,0], marker='x',label='$\ell$={}'.format(sigfig.round(lengthscale_parameter[index_of_tuples_passed[z][0],0],sigfigs=3))) 
        plt.xlabel('Number of Particles $[-]$', fontsize=fontsize)
        plt.ylabel('$\\frac{\Delta t}{\Delta t_{MD}}\ [-]$', rotation='horizontal',labelpad=24, fontsize=fontsize)
        plt.legend(loc='best', fontsize=fontsize)
        

#%% Selecting the solutions 
<<<<<<< HEAD
solution_choice_tuple=0
=======
solution_choice_tuple=2
>>>>>>> parent of 801a967 (This actually is the final version)
solution_choice=0
locations_of_non_nan_neg_select=locations_of_non_nan_neg[solution_choice_tuple][solution_choice]##
solution_row=locations_of_non_nan_neg_select[0]
solution_column=locations_of_non_nan_neg_select[1]
mean_free_path_pf_SRD_particles_cp_mthd_1_neg_in=mean_free_path_pf_SRD_particles_cp_mthd_1_neg[solution_choice_tuple ][solution_row,solution_column]
Number_MD_steps_per_SRD_with_pf_cp_mthd_1_neg_in=Number_MD_steps_per_SRD_with_pf_cp_mthd_1_neg[solution_choice_tuple ][solution_row,solution_column]
number_SRD_particles_wrt_pf_cp_mthd_1_neg_in=number_SRD_particles_wrt_pf_cp_mthd_1_neg[solution_choice_tuple ][solution_row,solution_column]
SRD_box_size_wrt_solid_beads_in=SRD_box_size_wrt_solid_beads[solution_choice_tuple ][solution_column]
mass_fluid_particle_wrt_pf_cp_mthd_1_in=(mass_fluid_particle_wrt_pf_cp_mthd_1[solution_row,solution_column])/(SRD_mass_scale_parameter[solution_choice_tuple ,0])
lengthscale_parameter_in=lengthscale_parameter[solution_choice_tuple ][0]

print("Mean free Path: ",mean_free_path_pf_SRD_particles_cp_mthd_1_neg_in)
print("SRD MD ratio : ",Number_MD_steps_per_SRD_with_pf_cp_mthd_1_neg_in)
print("SRD particle count:", number_SRD_particles_wrt_pf_cp_mthd_1_neg_in)
print("Collision cell size:",SRD_box_size_wrt_solid_beads_in)
print("Mass fluid particle:", mass_fluid_particle_wrt_pf_cp_mthd_1_in)
print("Simulation domain size:",box_side_length_scaled[solution_choice_tuple,0])
print("Check M>=10",( number_SRD_particles_wrt_pf_cp_mthd_1_neg_in/((box_side_length_scaled[solution_choice_tuple,0])**3/(SRD_box_size_wrt_solid_beads_in**3))))

#%% Produce run files 
from sim_file_producer_SRD import sim_file_prod_neg_soln
prod_run_file_name=fluid_name+'_prod_run_1_box_'+str(box_side_length_scaled) 
num_proc=4
total_no_realisations_per_solution=9 
np_req=str(total_no_realisations_per_solution*num_proc)
wd_path='/home/ucahlrl/Scratch/output/'
extra_code='module load mpi/intel/2018/update3/intel\n'
data_transfer_instructions=''
i_=0
j_=3
#laptop path 
#Path_2_shell_scirpts='/Users/lukedebono/documents/LAMMPS_projects_mac_book/OneDrive_1_24-02-2023/Shell_scripts_for_MYRIAD'
#imac path 
Path_2_shell_scirpts='/Volumes/Backup Plus 1/PhD_/Rouse Model simulations/Using LAMMPS imac/Shell_scripts_for_MYRIAD'
abs_path_2_lammps_exec='/home/ucahlrl/simulation_run_folder/lammps-23Jun2022/src/lmp_mpi'
abs_path_2_lammps_script='/home/ucahlrl/simulation_run_folder/no_wall_pure_SRD_sim_var_inputs_td_var_no_tstat_no_rescale_mom_output.file'
#laptop path 
#Path_2_generic='/Users/lukedebono/documents/LAMMPS_projects_mac_book/OneDrive_1_24-02-2023/Shell_scripts_for_MYRIAD'
#imac path 
Path_2_generic='/Volumes/Backup Plus 1/PhD_/Rouse Model simulations/Using LAMMPS imac/Shell_scripts_for_MYRIAD'

sim_file_prod_neg_soln(solution_choice_tuple,lengthscale_parameter_in,data_transfer_instructions,extra_code,wd_path,np_req,num_task_req,tempdir_req,wall_time,ram_requirement,prod_run_file_name,realisation_index_,equilibration_timesteps,VP_ave_freq,abs_path_2_lammps_exec,abs_path_2_lammps_script,num_proc,no_timesteps,thermo_freq,dump_freq,SRD_box_size_wrt_solid_beads_in,mean_free_path_pf_SRD_particles_cp_mthd_1_neg_in,scaled_timestep,mass_fluid_particle_wrt_pf_cp_mthd_1_in,Number_MD_steps_per_SRD_with_pf_cp_mthd_1_neg_in,number_SRD_particles_wrt_pf_cp_mthd_1_neg_in,swap_number,i_,j_,swap_rate,box_side_length_scaled[solution_choice_tuple,0],scaled_temp,eta_s,Path_2_shell_scirpts,Path_2_generic,fluid_name)
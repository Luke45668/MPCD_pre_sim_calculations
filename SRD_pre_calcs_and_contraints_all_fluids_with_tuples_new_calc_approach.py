#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 14 13:20:52 2023

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

# fixed values 
#######################################################################################################################################################################################################################################################################################################################################################################################################################################################################################
# Fixed Values for all simulations #####
#######################################################################################################################################################################################################################################################################################################################################################################################################################################################################################

equilibration_timesteps= 1000 # number of steps to do equilibration with 
VP_ave_freq =1000
chunk = 20
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
atol=0.01
rtol=0.00001
# determine side length of simulation box
r_particle =50e-6
i=0
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

#######################################################################################################################################################################################################################################################################################################################################################################################################################################################################################
# Start of N2 Calculations #####
#######################################################################################################################################################################################################################################################################################################################################################################################################################################################################################
#%%
# fixed values for nitrogen 
fluid_name='Nitrogen'
scaled_timestep=0.01
rho_s = 847 #kg/m^3
Temp_visc_multiplier=0.0000046059
T_K=72.2 *  Temp_visc_multiplier#+273.15 #Kelvin
k_b= 1.380649e-23 #boltzmann in J K^-1
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
#%%
# the length multplier is the key var to chnage 
number_of_lengthscales=200

sc_pos_soln=()
sc_neg_soln=()

mean_free_path_pf_SRD_particles_cp_mthd_1_neg=()
mean_free_path_to_box_ratio_neg=()
mean_free_path_pf_SRD_particles_cp_mthd_1_pos=()
mean_free_path_to_box_ratio_pos=()
Number_MD_steps_per_SRD_with_pf_cp_mthd_1_neg=()
Number_MD_steps_per_SRD_with_pf_cp_mthd_1_pos=()

number_SRD_particles_wrt_pf_cp_mthd_1_pos=()
number_SRD_particles_wrt_pf_cp_mthd_1_neg=()
#mass_fluid_particle_wrt_pf_cp_mthd_1=()
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
#scaled_temp=np.zeros((1,number_of_lengthscales))
box_side_length_scaled=()
box_size_vec_nd=()


# optimal range
 

length_multiplier=np.repeat(np.array([np.logspace(-2.5,-1.5,number_of_lengthscales)]).T,number_boxes_var,axis=1)
#length_multiplier=np.repeat(np.array([np.logspace(-2.5,-1.5,number_of_lengthscales)]).T,number_boxes_var,axis=1)
lengthscale_parameter = length_multiplier*r_particle
box_side_length_scaled=(box_side_length/lengthscale_parameter)
box_size_to_lengthscale=box_size_vec/lengthscale_parameter
mass_multiplier=10000000
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
    

    
#%% Plotting SRD_MD vs lengthscale
# 
plt.rcParams.update({
    "text.usetex": True,
    "font.family": "Helvetica"
})
#SRD_MD_ratio_vs_ell(lengthscale_parameter,fluid_name,number_of_test_points,SRD_MD_ratio_neg[0],SRD_MD_ratio_pos[0])


fig=plt.figure(figsize=(18,7)) #width x height
gs=GridSpec(nrows=1,ncols=2)

#fig.suptitle(fluid_name+':  $\\frac{\Delta t_{SRD}}{\Delta t_{MD}}$ vs ${\ell}\$ vs  $Sc$',size='x-large', wrap=True)
#$\\frac{\lambda}{\Delta x}\ $
ax1= fig.add_subplot(gs[0,0]) 
#ax2= fig.add_subplot(gs[0,1]) 
for z in range(0,number_of_lengthscales):
    
    ax1.plot(lengthscale_parameter[z,:],SRD_MD_ratio_neg[z][0,:])
    #ax2.plot(lengthscale_parameter[z,:],SRD_MD_ratio_pos[z,:],marker ='o')
    
    #ax1.legend(Solvent_bead_SRD_box_density_cp_1[0,z])
# ax1.plot(mean_free_path_to_box_ratio_pos[z,:],SRD_MD_ratio_pos[z,:],sc_pos_soln[z,:])
    
    ax1.set_xscale('log')
    # ax1.set_yscale('log')
    # ax1.set_zscale('log')
    ax1.set_xlabel('${\ell}\  $', rotation='horizontal',ha='right',size='large')
    ax1.set_ylabel( '$\\frac{\Delta t_{SRD}}{\Delta t_{MD}}$', rotation=0,ha='right',size='large')
    
    #ax2.grid('on')
    #ax2.set_xlabel('${\ell}\ [] $', rotation='horizontal',ha='right',size='large')
    #ax2.set_ylabel( '$\\frac{\Delta t_{SRD}}{\Delta t_{MD}}$', rotation='vertical',ha='right',size='large')
    
    #ax2.grid('on')
    
    
plt.show()
#%%       
 # now apply constraints
from MPCD_constraints_on_solutions import MPCD_constraints 
srd_ratio_tolerance=150
max_particle_count =15000000
min_particle_count=500
count_passed_constraints_neg=[]
count_passed_constraints_pos=[]
locations_of_non_nan_neg=()
locations_of_non_nan_pos=()

for z in range(0,number_of_lengthscales):
    
    MPCD_constraints(no_timesteps,min_particle_count,sc_neg_soln[z],sc_pos_soln[z],srd_ratio_tolerance,max_particle_count,number_SRD_particles_wrt_pf_cp_mthd_1_pos[z],number_SRD_particles_wrt_pf_cp_mthd_1_neg[z],mean_free_path_pf_SRD_particles_cp_mthd_1_neg[z],mean_free_path_pf_SRD_particles_cp_mthd_1_pos[z],Number_MD_steps_per_SRD_with_pf_cp_mthd_1_pos[z],Number_MD_steps_per_SRD_with_pf_cp_mthd_1_neg[z],Solvent_bead_SRD_box_density_cp_1,tolerance,SRD_box_size_wrt_solid_beads[z],comparison_pos[z],comparison_neg[z])
    count_passed_constraints_neg.append(np.count_nonzero(~np.isnan(Number_MD_steps_per_SRD_with_pf_cp_mthd_1_neg[z]))) 
    count_passed_constraints_pos.append(np.count_nonzero(~np.isnan(Number_MD_steps_per_SRD_with_pf_cp_mthd_1_pos[z])) )
  
    locations_of_non_nan_neg= locations_of_non_nan_neg+(np.argwhere(~np.isnan(Number_MD_steps_per_SRD_with_pf_cp_mthd_1_neg[z])),)
    locations_of_non_nan_pos= locations_of_non_nan_pos+(np.argwhere(~np.isnan(Number_MD_steps_per_SRD_with_pf_cp_mthd_1_pos[z])),)

#%%
#plot the count vs the value of ell
lengthscale_parameter=r_particle * length_multiplier
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
    ax1.set_ylabel('$C_{p,s}[-]$',rotation='horizontal')
    ax1.set_xlabel('$\ell$ [-]')
    ax1.plot(lengthscale_parameter[:,0],count_passed_constraints_neg[:])#, marker='o',s=5)
plt.show()

#%% Selecting the solution from passed solutions
from sim_file_producer_SRD import sim_file_prod_neg_soln

wall_time='8:00:00'
ram_requirement='8G'# per task 
tempdir_req='50G'
num_task_req=''
num_proc=4
total_no_realisations_per_solution=9 
np_req=str(total_no_realisations_per_solution*num_proc) # max value 36 for MYRIAD
wd_path='/home/ucahlrl/Scratch/output/' #simulation_batch_validations_'+'_fluid_visc_'+str(eta_s)+'_temp_'+str(scaled_temp)+'_box_size_'+str(box_side_length_scaled)+'_no_swap_freqs_'+str(swap_rate.size)+'_no_test_points_'+str(number_of_test_points)+'_'+META_DATA 
extra_code='module load mpi/intel/2018/update3/intel\n'
data_transfer_instructions=''
i_=0
j_=3
solution_choice_tuple=1 #129 for 0.005
# for results where sol count is >1 
# solution choice from count of passed solutions 
solution_choice=0
locations_of_non_nan_neg_select=locations_of_non_nan_neg[solution_choice_tuple][solution_choice]##
solution_row=locations_of_non_nan_neg_select[0]
solution_column=locations_of_non_nan_neg_select[1]

# paths and file names 
prod_run_file_name=fluid_name+'_prod_run_1_box_'+str(box_side_length_scaled) 
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
print("Solution choice:", solution_choice_tuple)
#%% produce myriad files
sim_file_prod_neg_soln(solution_choice_tuple,lengthscale_parameter_in,data_transfer_instructions,extra_code,wd_path,np_req,num_task_req,tempdir_req,wall_time,ram_requirement,prod_run_file_name,realisation_index_,equilibration_timesteps,VP_ave_freq,abs_path_2_lammps_exec,abs_path_2_lammps_script,num_proc,no_timesteps,thermo_freq,dump_freq,SRD_box_size_wrt_solid_beads_in,mean_free_path_pf_SRD_particles_cp_mthd_1_neg_in,scaled_timestep,mass_fluid_particle_wrt_pf_cp_mthd_1_in,Number_MD_steps_per_SRD_with_pf_cp_mthd_1_neg_in,number_SRD_particles_wrt_pf_cp_mthd_1_neg_in,swap_number,i_,j_,swap_rate,box_side_length_scaled[solution_choice_tuple,0],scaled_temp,eta_s,Path_2_shell_scirpts,Path_2_generic,fluid_name)
#######################################################################################################################################################################################################################################################################################################################################################################################################################################################################################
# End of Nitrogen Calculations #####
#######################################################################################################################################################################################################################################################################################################################################################################################################################################################################################
#######################################################################################################################################################################################################################################################################################################################################################################################################################################################################################
# Start of Ar Calculations #####
#######################################################################################################################################################################################################################################################################################################################################################################################################################################################################################

#%% Argon Calculations 
# define all inputs for Argon 
rho_s = 1426.9#621 #kg/m^3
r_particle =50e-6 #m 
#T_cel=34.5 #celsius, chosen from paper above 
Temp_visc_multiplier=0.000099
T_K=86.5 * Temp_visc_multiplier#+273.15 #Kelvin
k_b= 1.380649e-23 #boltzmann in J K^-1
eta_s_NIST=0.00029800 #Pa s


eta_s=eta_s_NIST* Temp_visc_multiplier#*1000 #*1000 to convert kg to g
nu_s = eta_s/rho_s
rho_particle = 1200 #kg m^-3 PMMA spheres
mass_solid_particle= rho_particle * (4/3)*np.pi*(r_particle**3)
# calculating stokes number in fluid conditions for solid particle tests
Stokes_number=0.0001
Gamma_dot= 4.5*Stokes_number*eta_s_NIST/ (rho_particle * r_particle**2)
fluid_name='Ar'

box_size_vec = np.array([box_side_length/number_boxes_vec])
mass_fluid_particle_wrt_pf_cp_mthd_1=(rho_s * (box_size_vec**3))/Solvent_bead_SRD_box_density_cp_1.T
#mass_fluid_particle_wrt_pf_cp_mthd_1=(rho_s * (box_size_vec**3))/Solvent_bead_SRD_box_density_cp_1.T

#%% 
# the length multplier is the key var to chnage 
number_of_lengthscales=200
scaled_timestep=0.1

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
#mass_fluid_particle_wrt_pf_cp_mthd_1=()
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
#length_multiplier=np.repeat(np.array([np.linspace(0.0000000001,0.000001,number_of_lengthscales)]).T,number_boxes_var,axis=1)
length_multiplier=np.repeat(np.array([np.logspace(-3,-1.5,number_of_lengthscales)]).T,number_boxes_var,axis=1)
lengthscale_parameter = length_multiplier*r_particle
box_side_length_scaled=(box_side_length/lengthscale_parameter)
box_size_to_lengthscale=box_size_vec/lengthscale_parameter
mass_multiplier=1000000
SRD_mass_scale_parameter = mass_multiplier* rho_s * (lengthscale_parameter**3)
r_particle_scaled = r_particle/lengthscale_parameter

box_size_vec = np.array([box_side_length/number_boxes_vec])
box_size_vec_nd=box_side_length_scaled/number_boxes_vec
#SRD_box_size_wrt_solid_beads=box_size_vec_nd
SRD_box_size_wrt_solid_beads_check=box_size_vec

for z in range(0,number_of_lengthscales):
    #  = lengthscale_parameter[0,z]
    # box_side_length_scaled=(box_side_length/lengthscale_parameter)
    # box_size_to_lengthscale=box_size_vec/lengthscale_parameter
    # mass_multiplier=10000000
    # SRD_mass_scale_parameter = mass_multiplier* rho_s * (lengthscale_parameter**3)
    # r_particle_scaled = r_particle/lengthscale_parameter

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

   #box_size_vec = np.array([box_side_length/number_boxes_vec])
    #box_size_vec_nd=box_size_vec_nd+(np.array([box_side_length_scaled[z,0]/number_boxes_vec]),)
    #number_of_boxes_in_each_dim=number_boxes_vec
    SRD_box_size_wrt_solid_beads= SRD_box_size_wrt_solid_beads+ (box_size_vec_nd[z,:],)
    #SRD_box_size_wrt_solid_beads_check=SRD_box_size_wrt_solid_beads_check+(box_size_vec,)



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

    # mass_fluid_particle_wrt_pf_cp_mthd_1[z]=SRD_non_dimensional_master_data[8]

    comparison_neg=   comparison_neg+(SRD_non_dimensional_master_data[6],)
    comparison_pos=  comparison_pos+(SRD_non_dimensional_master_data[7],)

    SRD_timestep_cp_1_based_on_sphere_pf_neg_nd=SRD_timestep_cp_1_based_on_sphere_pf_neg_nd+(SRD_non_dimensional_master_data[8],)
    SRD_MD_ratio_neg=SRD_MD_ratio_neg + ((SRD_timestep_cp_1_based_on_sphere_pf_neg_nd[z]/scaled_timestep),)
    SRD_step_neg_nd=SRD_timestep_cp_1_based_on_sphere_pf_neg_nd
    SRD_timestep_cp_1_based_on_sphere_pf_pos_nd= SRD_timestep_cp_1_based_on_sphere_pf_pos_nd+(SRD_non_dimensional_master_data[9],)
    SRD_step_pos_nd=SRD_timestep_cp_1_based_on_sphere_pf_pos_nd
    SRD_MD_ratio_pos=SRD_MD_ratio_pos+ ((SRD_timestep_cp_1_based_on_sphere_pf_pos_nd[z]/scaled_timestep),)
#%%
# doing all plots 
plt.rcParams.update({
    "text.usetex": True,
    "font.family": "Helvetica"
})
sc_vs_mfp_to_collision_cell_ratio(np.log(length_multiplier),number_of_lengthscales,fluid_name,number_of_test_points,np.log(mean_free_path_to_box_ratio_neg),np.log(sc_neg_soln),np.log(mean_free_path_to_box_ratio_pos),np.log(sc_pos_soln),Solvent_bead_SRD_box_density_cp_1)
# sc_vs_collision_cell_to_lengthscale(fluid_name,number_of_test_points,box_size_to_lengthscale,sc_neg_soln,sc_pos_soln,Solvent_bead_SRD_box_density_cp_1)
# mfp_to_collision_cell_vs_collision_cell_to_lengthscale(fluid_name,number_of_test_points,box_size_to_lengthscale,mean_free_path_to_box_ratio_neg)
# SRD_timestep_vs_collsion_cell(fluid_name,number_of_test_points,box_size_to_lengthscale,Solvent_bead_SRD_box_density_cp_1,SRD_step_pos_nd,SRD_step_neg_nd)
# mfp_to_collsion_cell_vs_SRD_MD_ratio_vs_Sc(fluid_name,number_of_test_points,mean_free_path_to_box_ratio_neg,mean_free_path_to_box_ratio_pos,SRD_MD_ratio_neg,SRD_MD_ratio_pos,sc_neg_soln,sc_pos_soln)
#%%       
 # now apply constraints
from MPCD_constraints_on_solutions import MPCD_constraints 
srd_ratio_tolerance=150
max_particle_count =1500000
min_particle_count=500
count_passed_constraints_neg=[]
count_passed_constraints_pos=[]
locations_of_non_nan_neg=()
locations_of_non_nan_pos=()

for z in range(0,number_of_lengthscales):
    
    MPCD_constraints(no_timesteps,min_particle_count,sc_neg_soln[z],sc_pos_soln[z],srd_ratio_tolerance,max_particle_count,number_SRD_particles_wrt_pf_cp_mthd_1_pos[z],number_SRD_particles_wrt_pf_cp_mthd_1_neg[z],mean_free_path_pf_SRD_particles_cp_mthd_1_neg[z],mean_free_path_pf_SRD_particles_cp_mthd_1_pos[z],Number_MD_steps_per_SRD_with_pf_cp_mthd_1_pos[z],Number_MD_steps_per_SRD_with_pf_cp_mthd_1_neg[z],Solvent_bead_SRD_box_density_cp_1,tolerance,SRD_box_size_wrt_solid_beads[z],comparison_pos[z],comparison_neg[z])
    #print("count_passed_constraints_neg "+str(count_passed_constraints_neg))
    count_passed_constraints_neg.append(np.count_nonzero(~np.isnan(Number_MD_steps_per_SRD_with_pf_cp_mthd_1_neg[z])))
    count_passed_constraints_pos.append(np.count_nonzero(~np.isnan(Number_MD_steps_per_SRD_with_pf_cp_mthd_1_pos[z])) )
    # this counts the non-nan values of the array by inverting the true false routine of .isnan with a ~ so now false are 1s and trues are 0 
    #count_passed_constraints_pos=np.zeros((SRD_mass_scale_parameter.size))
    #count_passed_constraints_pos.append(np.count_nonzero(~np.isnan(Number_MD_steps_per_SRD_with_pf_cp_mthd_1_pos[z])) )
    #print("count_passed_constraints_pos "+str(count_passed_constraints_pos))

    locations_of_non_nan_neg= locations_of_non_nan_neg+(np.argwhere(~np.isnan(Number_MD_steps_per_SRD_with_pf_cp_mthd_1_neg[z])),)
    locations_of_non_nan_pos= locations_of_non_nan_pos+(np.argwhere(~np.isnan(Number_MD_steps_per_SRD_with_pf_cp_mthd_1_pos[z])),)
    
#%%
#plot the count vs the value of ell
lengthscale_parameter=r_particle * length_multiplier
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
#%% Plotting SRD_MD vs lengthscale
# 
plt.rcParams.update({
    "text.usetex": True,
    "font.family": "Helvetica"
})
#SRD_MD_ratio_vs_ell(lengthscale_parameter,fluid_name,number_of_test_points,SRD_MD_ratio_neg[0],SRD_MD_ratio_pos[0])


fig=plt.figure(figsize=(18,7)) #width x height
gs=GridSpec(nrows=1,ncols=2)

#fig.suptitle(fluid_name+':  $\\frac{\Delta t_{SRD}}{\Delta t_{MD}}$ vs ${\ell}\$ vs  $Sc$',size='x-large', wrap=True)
#$\\frac{\lambda}{\Delta x}\ $
ax1= fig.add_subplot(gs[0,0]) 
#ax2= fig.add_subplot(gs[0,1]) 
for z in range(0,number_of_lengthscales):
    
    ax1.plot(lengthscale_parameter[z,:],SRD_MD_ratio_neg[z][0,:])
    #ax2.plot(lengthscale_parameter[z,:],SRD_MD_ratio_pos[z,:],marker ='o')
    
    #ax1.legend(Solvent_bead_SRD_box_density_cp_1[0,z])
# ax1.plot(mean_free_path_to_box_ratio_pos[z,:],SRD_MD_ratio_pos[z,:],sc_pos_soln[z,:])
    
    ax1.set_xscale('log')
    # ax1.set_yscale('log')
    # ax1.set_zscale('log')
    ax1.set_xlabel('${\ell}\  $', rotation='horizontal',ha='right',size='large')
    ax1.set_ylabel( '$\\frac{\Delta t_{SRD}}{\Delta t_{MD}}$', rotation=0,ha='right',size='large')
    
    #ax2.grid('on')
    #ax2.set_xlabel('${\ell}\ [] $', rotation='horizontal',ha='right',size='large')
    #ax2.set_ylabel( '$\\frac{\Delta t_{SRD}}{\Delta t_{MD}}$', rotation='vertical',ha='right',size='large')
    
    #ax2.grid('on')
    
    
plt.show()
#%% Produce the run files 
#%% Selecting the solution from passed solutions
from sim_file_producer_SRD import sim_file_prod_neg_soln

wall_time='8:00:00'
ram_requirement='8G'# per task 
tempdir_req='50G'
num_task_req=''
num_proc=4
total_no_realisations_per_solution=9 
np_req=str(total_no_realisations_per_solution*num_proc) # max value 36 for MYRIAD
wd_path='/home/ucahlrl/Scratch/output/' #simulation_batch_validations_'+'_fluid_visc_'+str(eta_s)+'_temp_'+str(scaled_temp)+'_box_size_'+str(box_side_length_scaled)+'_no_swap_freqs_'+str(swap_rate.size)+'_no_test_points_'+str(number_of_test_points)+'_'+META_DATA 
extra_code='module load mpi/intel/2018/update3/intel\n'
data_transfer_instructions=''
i_=0
j_=3
solution_choice_tuple=2 #105 for 0.005 runs 
# for results where sol count is >1 
# solution choice from count of passed solutions 
solution_choice=0
locations_of_non_nan_neg_select=locations_of_non_nan_neg[solution_choice_tuple][solution_choice]##
solution_row=locations_of_non_nan_neg_select[0]
solution_column=locations_of_non_nan_neg_select[1]

# paths and file names 
prod_run_file_name=fluid_name+'_prod_run_1_box_'+str(box_side_length_scaled) 
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
#%% produce myriad files
sim_file_prod_neg_soln(solution_choice_tuple,lengthscale_parameter_in,data_transfer_instructions,extra_code,wd_path,np_req,num_task_req,tempdir_req,wall_time,ram_requirement,prod_run_file_name,realisation_index_,equilibration_timesteps,VP_ave_freq,abs_path_2_lammps_exec,abs_path_2_lammps_script,num_proc,no_timesteps,thermo_freq,dump_freq,SRD_box_size_wrt_solid_beads_in,mean_free_path_pf_SRD_particles_cp_mthd_1_neg_in,scaled_timestep,mass_fluid_particle_wrt_pf_cp_mthd_1_in,Number_MD_steps_per_SRD_with_pf_cp_mthd_1_neg_in,number_SRD_particles_wrt_pf_cp_mthd_1_neg_in,swap_number,i_,j_,swap_rate,box_side_length_scaled[solution_choice_tuple,0],scaled_temp,eta_s,Path_2_shell_scirpts,Path_2_generic,fluid_name)
#######################################################################################################################################################################################################################################################################################################################################################################################################################################################################################
# End of Ar Calculations #####
#######################################################################################################################################################################################################################################################################################################################################################################################################################################################################################
#######################################################################################################################################################################################################################################################################################################################################################################################################################################################################################
# Start of Water Calculations #####
#######################################################################################################################################################################################################################################################################################################################################################################################################################################################################################
#%%
###NOTE TO Self: Water seems particularly hard to scale with MPCD, the solutions are far from integer values of SRD timestep
fluid_name='Water'
tolerance=0.01

rho_s = 1005##kg/m^3
r_particle =50e-6 #m 
Temp_visc_multiplier=1.612e-6#099 
T_K=300* Temp_visc_multiplier#+273.15 #Kelvin
k_b= 1.380649e-23 #boltzmann in J K^-1
eta_s_NIST=0.00085253*Temp_visc_multiplier

#determine side length of simulaton box 

eta_s=eta_s_NIST#*1000 #*1000 to convert kg to g
nu_s = eta_s/rho_s
rho_particle = 1200 #kg m^-3 PMMA spheres

mass_solid_particle= rho_particle * (4/3)*np.pi*(r_particle**3)
# calculating stokes number in fluid conditions for solid particle tests
Stokes_number=0.0001
Gamma_dot= 4.5*Stokes_number*eta_s_NIST/ (rho_particle * r_particle**2)
box_size_vec = np.array([box_side_length/number_boxes_vec])
mass_fluid_particle_wrt_pf_cp_mthd_1=(rho_s * (box_size_vec**3))/Solvent_bead_SRD_box_density_cp_1.T

# the length multplier is the key var to chnage 
number_of_lengthscales=200
scaled_timestep=0.01
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
#mass_fluid_particle_wrt_pf_cp_mthd_1=()
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
#scaled_temp=np.zeros((1,number_of_lengthscales))
box_side_length_scaled=()
box_size_vec_nd=()


# optimal range
 

length_multiplier=np.repeat(np.array([np.logspace(-1,0,number_of_lengthscales)]).T,number_boxes_var,axis=1)
#length_multiplier=np.repeat(np.array([np.logspace(-2.5,-1.5,number_of_lengthscales)]).T,number_boxes_var,axis=1)
lengthscale_parameter = length_multiplier*r_particle
box_side_length_scaled=(box_side_length/lengthscale_parameter)
box_size_to_lengthscale=box_size_vec/lengthscale_parameter
mass_multiplier=100
SRD_mass_scale_parameter = mass_multiplier* rho_s * (lengthscale_parameter**3)
r_particle_scaled = r_particle/lengthscale_parameter

box_size_vec = np.array([box_side_length/number_boxes_vec])
box_size_vec_nd=box_side_length_scaled/number_boxes_vec
#SRD_box_size_wrt_solid_beads=box_size_vec_nd
SRD_box_size_wrt_solid_beads_check=box_size_vec

#length_multiplier=np.repeat(np.array([np.linspace(0.00000000001,0.00001,number_of_lengthscales)]).T,number_boxes_var,axis=1)
# good setting for the length multiplier above 

#length_multiplier=np.repeat(np.array([np.linspace(0.000000000001,1,number_of_lengthscales)]).T,number_boxes_var,axis=1)



for z in range(0,number_of_lengthscales):
    #  = lengthscale_parameter[0,z]
    # box_side_length_scaled=(box_side_length/lengthscale_parameter)
    # box_size_to_lengthscale=box_size_vec/lengthscale_parameter
    # mass_multiplier=10000000
    # SRD_mass_scale_parameter = mass_multiplier* rho_s * (lengthscale_parameter**3)
    # r_particle_scaled = r_particle/lengthscale_parameter

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

   #box_size_vec = np.array([box_side_length/number_boxes_vec])
    #box_size_vec_nd=box_size_vec_nd+(np.array([box_side_length_scaled[z,0]/number_boxes_vec]),)
    #number_of_boxes_in_each_dim=number_boxes_vec
    SRD_box_size_wrt_solid_beads= SRD_box_size_wrt_solid_beads+ (box_size_vec_nd[z,:],)
    #SRD_box_size_wrt_solid_beads_check=SRD_box_size_wrt_solid_beads_check+(box_size_vec,)



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

    # mass_fluid_particle_wrt_pf_cp_mthd_1[z]=SRD_non_dimensional_master_data[8]

    comparison_neg=   comparison_neg+(SRD_non_dimensional_master_data[6],)
    comparison_pos=  comparison_pos+(SRD_non_dimensional_master_data[7],)

    SRD_timestep_cp_1_based_on_sphere_pf_neg_nd=SRD_timestep_cp_1_based_on_sphere_pf_neg_nd+(SRD_non_dimensional_master_data[8],)
    SRD_MD_ratio_neg=SRD_MD_ratio_neg + ((SRD_timestep_cp_1_based_on_sphere_pf_neg_nd[z]/scaled_timestep),)
    SRD_step_neg_nd=SRD_timestep_cp_1_based_on_sphere_pf_neg_nd
    SRD_timestep_cp_1_based_on_sphere_pf_pos_nd= SRD_timestep_cp_1_based_on_sphere_pf_pos_nd+(SRD_non_dimensional_master_data[9],)
    SRD_step_pos_nd=SRD_timestep_cp_1_based_on_sphere_pf_pos_nd
    SRD_MD_ratio_pos=SRD_MD_ratio_pos+ ((SRD_timestep_cp_1_based_on_sphere_pf_pos_nd[z]/scaled_timestep),)
#%%
# doing all plots 
plt.rcParams.update({
    "text.usetex": True,
    "font.family": "Helvetica"
})
#sc_vs_mfp_to_collision_cell_ratio(np.log(length_multiplier),number_of_lengthscales,fluid_name,number_of_test_points,np.log(mean_free_path_to_box_ratio_neg),np.log(sc_neg_soln),np.log(mean_free_path_to_box_ratio_pos),np.log(sc_pos_soln),Solvent_bead_SRD_box_density_cp_1)
sc_vs_mfp_to_collision_cell_ratio(length_multiplier,number_of_lengthscales,fluid_name,number_of_test_points,mean_free_path_to_box_ratio_neg,sc_neg_soln,mean_free_path_to_box_ratio_pos,sc_pos_soln,Solvent_bead_SRD_box_density_cp_1)
#sc_vs_collision_cell_to_lengthscale(fluid_name,number_of_test_points,box_size_to_lengthscale,sc_neg_soln,sc_pos_soln,Solvent_bead_SRD_box_density_cp_1)
#mfp_to_collision_cell_vs_collision_cell_to_lengthscale(fluid_name,number_of_test_points,box_size_to_lengthscale,mean_free_path_to_box_ratio_neg)
#SRD_timestep_vs_collsion_cell(fluid_name,number_of_test_points,box_size_to_lengthscale,Solvent_bead_SRD_box_density_cp_1,SRD_step_pos_nd,SRD_step_neg_nd)
#mfp_to_collsion_cell_vs_SRD_MD_ratio_vs_Sc(fluid_name,number_of_test_points,mean_free_path_to_box_ratio_neg,mean_free_path_to_box_ratio_pos,SRD_MD_ratio_neg,SRD_MD_ratio_pos,sc_neg_soln,sc_pos_soln)
#%%       
 # now apply constraints
from MPCD_constraints_on_solutions import MPCD_constraints 
srd_ratio_tolerance=9
max_particle_count =1500000
min_particle_count=500
count_passed_constraints_neg=[]
count_passed_constraints_pos=[]
locations_of_non_nan_neg=()
locations_of_non_nan_pos=()

for z in range(0,number_of_lengthscales):
    
    MPCD_constraints(no_timesteps,min_particle_count,sc_neg_soln[z],sc_pos_soln[z],srd_ratio_tolerance,max_particle_count,number_SRD_particles_wrt_pf_cp_mthd_1_pos[z],number_SRD_particles_wrt_pf_cp_mthd_1_neg[z],mean_free_path_pf_SRD_particles_cp_mthd_1_neg[z],mean_free_path_pf_SRD_particles_cp_mthd_1_pos[z],Number_MD_steps_per_SRD_with_pf_cp_mthd_1_pos[z],Number_MD_steps_per_SRD_with_pf_cp_mthd_1_neg[z],Solvent_bead_SRD_box_density_cp_1,tolerance,SRD_box_size_wrt_solid_beads[z],comparison_pos[z],comparison_neg[z])
    count_passed_constraints_neg.append(np.count_nonzero(~np.isnan(Number_MD_steps_per_SRD_with_pf_cp_mthd_1_neg[z])))
    #print("count_passed_constraints_neg "+str(count_passed_constraints_neg))

    # this counts the non-nan values of the array by inverting the true false routine of .isnan with a ~ so now false are 1s and trues are 0 
    #count_passed_constraints_pos=np.zeros((SRD_mass_scale_parameter.size))
    count_passed_constraints_pos.append(np.count_nonzero(~np.isnan(Number_MD_steps_per_SRD_with_pf_cp_mthd_1_pos[z])) )
    #print("count_passed_constraints_pos "+str(count_passed_constraints_pos))

    locations_of_non_nan_neg= locations_of_non_nan_neg+(np.argwhere(~np.isnan(Number_MD_steps_per_SRD_with_pf_cp_mthd_1_neg[z])),)
    locations_of_non_nan_pos= locations_of_non_nan_pos+(np.argwhere(~np.isnan(Number_MD_steps_per_SRD_with_pf_cp_mthd_1_pos[z])),)

#%%
#plot the count vs the value of ell
lengthscale_parameter=r_particle * length_multiplier
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

#%% Selecting the solution from passed solutions
from sim_file_producer_SRD import sim_file_prod_neg_soln

wall_time='8:00:00'
ram_requirement='8G'# per task 
tempdir_req='50G'
num_task_req=''
num_proc=4
total_no_realisations_per_solution=9 
np_req=str(total_no_realisations_per_solution*num_proc) # max value 36 for MYRIAD
wd_path='/home/ucahlrl/Scratch/output/' #simulation_batch_validations_'+'_fluid_visc_'+str(eta_s)+'_temp_'+str(scaled_temp)+'_box_size_'+str(box_side_length_scaled)+'_no_swap_freqs_'+str(swap_rate.size)+'_no_test_points_'+str(number_of_test_points)+'_'+META_DATA 
extra_code='module load mpi/intel/2018/update3/intel\n'
data_transfer_instructions=''
i_=0
j_=3
solution_choice_tuple=5
# for results where sol count is >1 
# solution choice from count of passed solutions 
solution_choice=0
locations_of_non_nan_neg_select=locations_of_non_nan_neg[solution_choice_tuple][solution_choice]##
solution_row=locations_of_non_nan_neg_select[0]
solution_column=locations_of_non_nan_neg_select[1]

# paths and file names 
prod_run_file_name=fluid_name+'_prod_run_1_box_'+str(box_side_length_scaled) 
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
#%% produce myriad files
sim_file_prod_neg_soln(solution_choice_tuple,lengthscale_parameter_in,data_transfer_instructions,extra_code,wd_path,np_req,num_task_req,tempdir_req,wall_time,ram_requirement,prod_run_file_name,realisation_index_,equilibration_timesteps,VP_ave_freq,abs_path_2_lammps_exec,abs_path_2_lammps_script,num_proc,no_timesteps,thermo_freq,dump_freq,SRD_box_size_wrt_solid_beads_in,mean_free_path_pf_SRD_particles_cp_mthd_1_neg_in,scaled_timestep,mass_fluid_particle_wrt_pf_cp_mthd_1_in,Number_MD_steps_per_SRD_with_pf_cp_mthd_1_neg_in,number_SRD_particles_wrt_pf_cp_mthd_1_neg_in,swap_number,i_,j_,swap_rate,box_side_length_scaled[solution_choice_tuple,0],scaled_temp,eta_s,Path_2_shell_scirpts,Path_2_generic,fluid_name)
#######################################################################################################################################################################################################################################################################################################################################################################################################################################################################################
# End of Water Calculations #####
#######################################################################################################################################################################################################################################################################################################################################################################################################################################################################################
#######################################################################################################################################################################################################################################################################################################################################################################################################################################################################################
# Start of Cyclohex  Calculations #####
#######################################################################################################################################################################################################################################################################################################################################################################################################################################################################################
#%%
# tolerance=0.01
# number_of_test_points =50
# Solvent_bead_SRD_box_density_cp_1 = np.array([(np.linspace(3.5,1000,number_of_test_points))])
# number_of_M_cp_1=Solvent_bead_SRD_box_density_cp_1.shape[1]
# number_boxes_var=30000
# min_number_boxes_for_particle_size=23
# number_boxes_vec=np.linspace(min_number_boxes_for_particle_size,(min_number_boxes_for_particle_size-1)+number_boxes_var,number_boxes_var)

# rho_s = 764.95 #kg/m^3
# r_particle =50e-6 #m 
# T_cel=34.5 #celsius, chosen from paper above 
# Temp_visc_multiplier=0.0001
# T_K=T_cel+273.15 * Temp_visc_multiplier #Kelvin
# k_b= 1.380649e-23 #boltzmann in J K^-1
# eta_s_NIST=0.00076285*Temp_visc_multiplier #Pa s 


# eta_s=eta_s_NIST#*1000 #*1000 to convert kg to g
# nu_s = eta_s/rho_s
# rho_particle = 1200 #kg m^-3 PMMA spheres
# mass_solid_particle= rho_particle * (4/3)*np.pi*(r_particle**3)
# r_particle =50e-6
# phi=0.0000009
# N=2
# Vol_box_at_specified_phi= N* (4/3)*np.pi*r_particle**3 /phi
# box_side_length=np.cbrt(Vol_box_at_specified_phi)


# Stokes_number=0.0001
# Gamma_dot= 4.5*Stokes_number*eta_s_NIST/ (rho_particle * r_particle**2)
# box_size_vec = np.array([box_side_length/number_boxes_vec])
# mass_fluid_particle_wrt_pf_cp_mthd_1=(rho_s * (box_size_vec**3))/Solvent_bead_SRD_box_density_cp_1.T
# fluid_name='C6H12'

#######################################################################################################################################################################################################################################################################################################################################################################################################################################################################################
# End of Cyclohex  Calculations #####
#######################################################################################################################################################################################################################################################################################################################################################################################################################################################################################

#######################################################################################################################################################################################################################################################################################################################################################################################################################################################################################
# Start of hexane  Calculations #####
#######################################################################################################################################################################################################################################################################################################################################################################################################################################################################################
#%% 

rho_s = 700#621 #kg/m^3
r_particle =50e-6 #m 
#T_cel=34.5 #celsius, chosen from paper above 
Temp_visc_multiplier=0.00003
T_K=311* Temp_visc_multiplier#+273.15 #Kelvin
k_b= 1.380649e-23 #boltzmann in J K^-1
eta_s_NIST= 0.00046729*Temp_visc_multiplier	 #Pa s 

eta_s=eta_s_NIST#*1000 #*1000 to convert kg to g
nu_s = eta_s/rho_s
rho_particle = 1200 #kg m^-3 PMMA spheres
mass_solid_particle= rho_particle * (4/3)*np.pi*(r_particle**3)
# calculating stokes number in fluid conditions for solid particle tests
Stokes_number=0.0001
Gamma_dot= 4.5*Stokes_number*eta_s_NIST/ (rho_particle * r_particle**2)

r_particle =50e-6
phi=0.001
N=2
Vol_box_at_specified_phi= N* (4/3)*np.pi*r_particle**3 /phi
box_side_length=np.cbrt(Vol_box_at_specified_phi)
box_size_vec = np.array([box_side_length/number_boxes_vec])
mass_fluid_particle_wrt_pf_cp_mthd_1=(rho_s * (box_size_vec**3))/Solvent_bead_SRD_box_density_cp_1.T
fluid_name='C6H14'
#
# the length multplier is the key var to chnage 
number_of_lengthscales=200

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
#mass_fluid_particle_wrt_pf_cp_mthd_1=()
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
length_multiplier=np.repeat(np.array([np.logspace(-1.5,0,number_of_lengthscales)]).T,number_boxes_var,axis=1)
#length_multiplier=np.repeat(np.array([np.logspace(-2.5,-1.5,number_of_lengthscales)]).T,number_boxes_var,axis=1)
lengthscale_parameter = length_multiplier*r_particle
box_side_length_scaled=(box_side_length/lengthscale_parameter)
box_size_to_lengthscale=box_size_vec/lengthscale_parameter
mass_multiplier=100
SRD_mass_scale_parameter = mass_multiplier* rho_s * (lengthscale_parameter**3)
r_particle_scaled = r_particle/lengthscale_parameter

box_size_vec = np.array([box_side_length/number_boxes_vec])
box_size_vec_nd=box_side_length_scaled/number_boxes_vec
#SRD_box_size_wrt_solid_beads=box_size_vec_nd
SRD_box_size_wrt_solid_beads_check=box_size_vec



for z in range(0,number_of_lengthscales):
    #  = lengthscale_parameter[0,z]
    # box_side_length_scaled=(box_side_length/lengthscale_parameter)
    # box_size_to_lengthscale=box_size_vec/lengthscale_parameter
    # mass_multiplier=10000000
    # SRD_mass_scale_parameter = mass_multiplier* rho_s * (lengthscale_parameter**3)
    # r_particle_scaled = r_particle/lengthscale_parameter

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

   #box_size_vec = np.array([box_side_length/number_boxes_vec])
    #box_size_vec_nd=box_size_vec_nd+(np.array([box_side_length_scaled[z,0]/number_boxes_vec]),)
    #number_of_boxes_in_each_dim=number_boxes_vec
    SRD_box_size_wrt_solid_beads= SRD_box_size_wrt_solid_beads+ (box_size_vec_nd[z,:],)
    #SRD_box_size_wrt_solid_beads_check=SRD_box_size_wrt_solid_beads_check+(box_size_vec,)



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

    # mass_fluid_particle_wrt_pf_cp_mthd_1[z]=SRD_non_dimensional_master_data[8]

    comparison_neg=   comparison_neg+(SRD_non_dimensional_master_data[6],)
    comparison_pos=  comparison_pos+(SRD_non_dimensional_master_data[7],)

    SRD_timestep_cp_1_based_on_sphere_pf_neg_nd=SRD_timestep_cp_1_based_on_sphere_pf_neg_nd+(SRD_non_dimensional_master_data[8],)
    SRD_MD_ratio_neg=SRD_MD_ratio_neg + ((SRD_timestep_cp_1_based_on_sphere_pf_neg_nd[z]/scaled_timestep),)
    SRD_step_neg_nd=SRD_timestep_cp_1_based_on_sphere_pf_neg_nd
    SRD_timestep_cp_1_based_on_sphere_pf_pos_nd= SRD_timestep_cp_1_based_on_sphere_pf_pos_nd+(SRD_non_dimensional_master_data[9],)
    SRD_step_pos_nd=SRD_timestep_cp_1_based_on_sphere_pf_pos_nd
    SRD_MD_ratio_pos=SRD_MD_ratio_pos+ ((SRD_timestep_cp_1_based_on_sphere_pf_pos_nd[z]/scaled_timestep),)

#%%       
 # now apply constraints
from MPCD_constraints_on_solutions import MPCD_constraints 
srd_ratio_tolerance=200
max_particle_count =1.4e05
min_particle_count=500
count_passed_constraints_neg=[]
count_passed_constraints_pos=[]
locations_of_non_nan_neg=()
locations_of_non_nan_pos=()

for z in range(0,number_of_lengthscales):
    
    MPCD_constraints(no_timesteps,min_particle_count,sc_neg_soln[z],sc_pos_soln[z],srd_ratio_tolerance,max_particle_count,number_SRD_particles_wrt_pf_cp_mthd_1_pos[z],number_SRD_particles_wrt_pf_cp_mthd_1_neg[z],mean_free_path_pf_SRD_particles_cp_mthd_1_neg[z],mean_free_path_pf_SRD_particles_cp_mthd_1_pos[z],Number_MD_steps_per_SRD_with_pf_cp_mthd_1_pos[z],Number_MD_steps_per_SRD_with_pf_cp_mthd_1_neg[z],Solvent_bead_SRD_box_density_cp_1,tolerance,SRD_box_size_wrt_solid_beads[z],comparison_pos[z],comparison_neg[z])
    count_passed_constraints_neg.append(np.count_nonzero(~np.isnan(Number_MD_steps_per_SRD_with_pf_cp_mthd_1_neg[z])))
    #print("count_passed_constraints_neg "+str(count_passed_constraints_neg))

    # this counts the non-nan values of the array by inverting the true false routine of .isnan with a ~ so now false are 1s and trues are 0 
    #count_passed_constraints_pos=np.zeros((SRD_mass_scale_parameter.size))
    count_passed_constraints_pos.append(np.count_nonzero(~np.isnan(Number_MD_steps_per_SRD_with_pf_cp_mthd_1_pos[z])) )
    #print("count_passed_constraints_pos "+str(count_passed_constraints_pos))

    locations_of_non_nan_neg= locations_of_non_nan_neg+(np.argwhere(~np.isnan(Number_MD_steps_per_SRD_with_pf_cp_mthd_1_neg[z])),)
    locations_of_non_nan_pos= locations_of_non_nan_pos+(np.argwhere(~np.isnan(Number_MD_steps_per_SRD_with_pf_cp_mthd_1_pos[z])),)
#%%
#plot the count vs the value of ell
lengthscale_parameter=r_particle * length_multiplier
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
#%% Selecting the solution from passed solutions
from sim_file_producer_SRD import sim_file_prod_neg_soln

wall_time='8:00:00'
ram_requirement='8G'# per task 
tempdir_req='50G'
num_task_req=''
num_proc=4
total_no_realisations_per_solution=9 
np_req=str(total_no_realisations_per_solution*num_proc) # max value 36 for MYRIAD
wd_path='/home/ucahlrl/Scratch/output/' #simulation_batch_validations_'+'_fluid_visc_'+str(eta_s)+'_temp_'+str(scaled_temp)+'_box_size_'+str(box_side_length_scaled)+'_no_swap_freqs_'+str(swap_rate.size)+'_no_test_points_'+str(number_of_test_points)+'_'+META_DATA 
extra_code='module load mpi/intel/2018/update3/intel\n'
data_transfer_instructions=''
i_=0
j_=3
solution_choice_tuple=0  #84 for 0.005 
# for results where sol count is >1 
# solution choice from count of passed solutions 
solution_choice=0
locations_of_non_nan_neg_select=locations_of_non_nan_neg[solution_choice_tuple][solution_choice]##
solution_row=locations_of_non_nan_neg_select[0]
solution_column=locations_of_non_nan_neg_select[1]

# paths and file names 
prod_run_file_name=fluid_name+'_prod_run_1_box_'+str(box_side_length_scaled) 
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
#%% produce myriad files
sim_file_prod_neg_soln(solution_choice_tuple,lengthscale_parameter_in,data_transfer_instructions,extra_code,wd_path,np_req,num_task_req,tempdir_req,wall_time,ram_requirement,prod_run_file_name,realisation_index_,equilibration_timesteps,VP_ave_freq,abs_path_2_lammps_exec,abs_path_2_lammps_script,num_proc,no_timesteps,thermo_freq,dump_freq,SRD_box_size_wrt_solid_beads_in,mean_free_path_pf_SRD_particles_cp_mthd_1_neg_in,scaled_timestep,mass_fluid_particle_wrt_pf_cp_mthd_1_in,Number_MD_steps_per_SRD_with_pf_cp_mthd_1_neg_in,number_SRD_particles_wrt_pf_cp_mthd_1_neg_in,swap_number,i_,j_,swap_rate,box_side_length_scaled[solution_choice_tuple,0],scaled_temp,eta_s,Path_2_shell_scirpts,Path_2_generic,fluid_name)
#######################################################################################################################################################################################################################################################################################################################################################################################################################################################################################
# End of hexane  Calculations #####
#######################################################################################################################################################################################################################################################################################################################################################################################################################################################################################


# %%

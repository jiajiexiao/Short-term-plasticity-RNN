"""
Default parameters for training.
"""

import numpy as np
import tensorflow as tf

class Paramaters:
    
    def __init__(self):

        print('Initializing paramaters...')
        
        self.params = {
        'num_motion_tuned':      36,
        'num_fix_tuned':         0,
        'num_rule_tuned':        0,
        'num_exc_units':         40,
        'num_inh_units':         10,
        'n_output':              3,
        'dead_time':             400,
        'fix_time':              500,
        'sample_time':           500,
        'delay_time':            1000,
        'test_time':             500,
        'varialbe_delay_scale':  20,
        'variable_delay_max':    500,     
        'possible_rules':        [0],
        'clip_max_grad_val':     0.25,
        'learning_rate':         5e-3,
        'membrane_time_constant':100,
        'num_motion_dirs':       8,
        'input_mean':            0,
        'input_sd':              0.1,
        'noise_sd':              0.5,
        'connection_prob':       1,
        'dt':                    25,
        'catch_trial_pct':       0.2,
        'probe_trial_pct':       0,
        'probe_time':            25,
        'spike_cost':            5e-5,
        'wiring_cost':           5e-7,
        'match_test_prob':       0.3,
        'repeat_pct':            0.5,
        'max_num_tests':         4,
        'tau_fast':              200,
        'tau_slow':              1500,
        'U_stf':                 0.15,
        'U_std':                 0.45,
        'stop_perf_th':          1,
        'stop_error_th':         0.005,
        'batch_train_size':      128,
        'num_batches':           8,
        'num_iterations':        1500,
        'synapse_config':        None,
        'stimulus_type':         'motion',
        'load_previous_model':   False,
        'var_delay':             False,
        'save_dir':              'D:/Masse/RNN STP/saved_models/'
        }
    
           
        
    def return_params(self):
    
        # re-calculate all dependencies and initial values and return paramaters
        self.create_dependencies()
        self.initialize_weights_biases()
        self.initialize_synaptic_paramaters()
        self.define_neuron_location()
        
        return self.params
        

    def create_dependencies(self):
        
        """
        The ABBA task requires farily specific trial params to properly function
        Here, if the ABBA task is used, we will use the suggested defaults
        """
        if 4 in self.params['possible_rules']:
            print('Using suggested ABBA trial params...')
            stim_duration = 240
            self.params['ABBA_delay']  = stim_duration
            self.params['test_time']  = stim_duration
            self.params['sample_time']  = stim_duration
            self.params['delay_time']  = 8*stim_duration
            self.params['dt']  = 20
        
        self.params['n_input'] = self.params['num_motion_tuned'] + self.params['num_fix_tuned'] + self.params['num_rule_tuned']
        self.params['n_hidden'] = self.params['num_exc_units'] + self.params['num_inh_units']
       
        """
        If num_inh_units is set > 0, then neurons can be either excitatory or inihibitory; is num_inh_units = 0, 
        then the weights projecting from a single neuron can be a mixture of excitatory or inhibiotry
        """
        if self.params['num_inh_units'] > 0:
            self.params['EI'] = True
            print('Using EI network')
        else:
            self.params['EI'] = False
            print('Not using EI network')
        self.params['EI_list'] = np.ones((self.params['n_hidden']), dtype=np.float32)
        self.params['EI_list'][-self.params['num_inh_units']:] = -1
        self.params['EI_matrix'] = np.diag(self.params['EI_list'])
        
        self.params['shape'] = (self.params['n_input'], self.params['n_hidden'],self.params['n_output'])
        
        # rule cue will be presented during the 3rd quarter of the delay epoch
        self.params['rule_onset_time'] = (self.params['dead_time']+self.params['fix_time']+self.params['sample_time']+self.params['delay_time']//2)//self.params['dt']
        self.params['rule_offset_time'] = (self.params['dead_time']+self.params['fix_time']+self.params['sample_time']+3*self.params['delay_time']//4)//self.params['dt']
        

        self.params['trial_length'] = self.params['dead_time']+self.params['fix_time']+self.params['sample_time']+self.params['delay_time']+self.params['test_time'] 
        
        #self.params['trial_length'] = 135*20
        #print('HARD CODED Trial length: paramters.py')
        
        # Membrane time constant of RNN neurons
        self.params['alpha_neuron'] = self.params['dt']/self.params['membrane_time_constant']
        # The standard deviation of the gaussian noise added to each RNN neuron at each time step
        self.params['noise_sd'] = np.sqrt(2*self.params['alpha_neuron'])*self.params['noise_sd']
        # The time step in seconds
        self.params['dt_sec'] = np.float32(self.params['dt']/1000)
        # Number of time steps
        self.params['num_time_steps'] = self.params['trial_length']//self.params['dt']
        # The delay between test stimuli in the ABBA task (rule = 4)

    
    def initialize_weights_biases(self):

        """
        Initialize input weights 
        """   
        self.params['w_in0'] = np.float32(np.random.gamma(shape=0.25, scale=1.0, 
                                                          size=[self.params['n_hidden'],self.params['n_input']]))
        connection_present = np.random.rand(self.params['n_hidden'],self.params['n_input']) < self.params['connection_prob']
        self.params['w_in0'] *= connection_present
       
        """
        Initialize starting recurrent weights and biases
        """ 
        if self.params['EI']:
            #If excitatory/inhibitory neurons desired, initialize with random matrix with zeros on the diagonal
            self.params['w_rnn0'] = np.float32(np.random.gamma(shape=0.25, scale=1.0, 
                                                               size=[self.params['n_hidden'],self.params['n_hidden']]))
            connection_present = np.random.rand(self.params['n_hidden'],self.params['n_hidden']) < self.params['connection_prob']
            self.params['w_rnn0'] *= connection_present
            
            for j in range(self.params['n_hidden']):
                self.params['w_rnn0'][j,j] = 0
            ind_inh = np.where(self.params['EI_list']==-1)[0]
            sum_inh = np.sum(self.params['w_rnn0'][:,ind_inh])
            ind_exc = np.where(self.params['EI_list']==1)[0]
            sum_exc = np.sum(self.params['w_rnn0'][:,ind_exc])

            self.params['w_rec_mask'] = np.ones((self.params['n_hidden'],self.params['n_hidden']), dtype=np.float32) - np.eye(self.params['n_hidden'])
        else:
            # If excitatory/inhibitory neurons not desired, initialize with diagonal matrix
            self.params['w_rnn0'] = np.float32(0.975*np.identity(self.params['n_hidden']))
            self.params['w_rec_mask'] = np.ones((self.params['n_hidden'],self.params['n_hidden']), dtype=np.float32)
            
        self.params['b_rnn0'] = np.zeros((self.params['n_hidden'], 1), dtype=np.float32)
        
        # the effective synaptic weights are stronger when no short-term synaptic plasticity is used,
        # thus, we will reduce the strength of the recurrent weights to compensate
        if self.params['synapse_config'] == None:
            self.params['w_rnn0'] /= 3
 
        """
        Initialize output weights and biases
        """
        self.params['w_out0'] = np.float32(np.random.gamma(shape=0.25, scale=1.0, 
                                                           size=[self.params['n_output'],self.params['n_hidden']]))
        connection_present = np.random.rand(self.params['n_output'],self.params['n_hidden']) < self.params['connection_prob']
        self.params['w_out0'] *= connection_present
        self.params['b_out0'] = np.zeros((self.params['n_output'],1), dtype=np.float32)
        self.params['w_out_mask'] = np.ones((self.params['n_output'],self.params['n_hidden']), dtype=np.float32)
        if self.params['EI']:
            ind_inh = np.where(self.params['EI_list']==-1)[0]
            self.params['w_out0'][:, ind_inh] = 0
            self.params['w_out_mask'][:, ind_inh] = 0
             
    
    def initialize_synaptic_paramaters(self):

        """
        Define all paramaters needed for short-term synaptic plasticity
        0 = Static
        1 = Facilitating
        2 = Depressing
        """

        self.params['synapse_type']  = np.zeros((self.params['n_hidden']), dtype=np.int8)
        
        # only facilitating synapses
        if self.params['synapse_config'] == 'stf': 
            self.params['synapse_type'] = np.ones((self.params['n_hidden']), dtype=np.int8)

        # only depressing synapses
        elif self.params['synapse_config'] == 'std': 
            self.params['synapse_type'] = 2*np.ones((self.params['n_hidden']), dtype=np.int8)
         
        # even numbers will be facilitating, odd numbers will be depressing
        elif self.params['synapse_config'] == 'std_stf': 
            self.params['synapse_type'] = np.ones((self.params['n_hidden']), dtype=np.int8)
            ind = range(1,self.params['n_hidden'],2)
            self.params['synapse_type'][ind] = 2
            
        self.params['alpha_stf'] = np.ones((self.params['n_hidden'], 1), dtype=np.float32)
        self.params['alpha_std'] = np.ones((self.params['n_hidden'], 1), dtype=np.float32)
        self.params['U'] = np.ones((self.params['n_hidden'], 1), dtype=np.float32)
        
        # initial synaptic values
        self.params['syn_x_init'] = np.zeros((self.params['n_hidden'], self.params['batch_train_size']), dtype=np.float32)
        self.params['syn_u_init'] = np.zeros((self.params['n_hidden'], self.params['batch_train_size']), dtype=np.float32)
        # initial hidden state
        self.params['h_init'] = 0.1*np.ones((self.params['n_hidden'], self.params['batch_train_size']), dtype=np.float32)
        
        for i in range(self.params['n_hidden']):  
            if self.params['synapse_type'][i] == 1:
                self.params['alpha_stf'][i,0] = self.params['dt']/self.params['tau_slow']
                self.params['alpha_std'][i,0] = self.params['dt']/self.params['tau_fast']
                self.params['U'][i,0] = 0.15
                self.params['syn_x_init'][i,:] = 1
                self.params['syn_u_init'][i,:] = self.params['U'][i,0]
                
            elif self.params['synapse_type'][i] == 2:
                self.params['alpha_stf'][i,0] = self.params['dt']/self.params['tau_fast']
                self.params['alpha_std'][i,0] = self.params['dt']/self.params['tau_slow']
                self.params['U'][i,0] = 0.45
                self.params['syn_x_init'][i,:] = 1
                self.params['syn_u_init'][i,:] = self.params['U'][i,0]
                
        """
        CAN DELETE
        THIS WAS USED when trying to get RNNCell working
        self.params['alpha_stf'] = self.params['alpha_stf'].transpose()        
        self.params['alpha_std'] = self.params['alpha_std'].transpose()  
        self.params['U'] = self.params['U'].transpose() 
        """
        self.params['alpha_stf'] = self.params['alpha_stf'].transpose()        
        self.params['alpha_std'] = self.params['alpha_std'].transpose()  
        self.params['U'] = self.params['U'].transpose() 
        self.params['w_in0'] = self.params['w_in0'].transpose() 
        self.params['b_rnn0'] = self.params['b_rnn0'].transpose() 
        self.params['w_out0'] = self.params['w_out0'].transpose() 
        self.params['b_out0'] = self.params['b_out0'].transpose() 
        self.params['h_init'] = self.params['h_init'].transpose() 
        self.params['syn_x_init'] = self.params['syn_x_init'].transpose() 
        self.params['syn_u_init'] = self.params['syn_u_init'].transpose() 
                
    def define_neuron_location(self):
        
        """
        Not currently being used
        This will eventually be used to implement a penalty term on long-distance projections
        Based on work by Jeff Clune
        """
        
        coord = np.zeros((self.params['n_hidden'],2))
        
        # determine the smallest square that woudl contain all the neurons
        n = int(np.ceil(np.sqrt(self.params['n_hidden'])))
        possible_locs = []
        [possible_locs.append([i,j]) for i in range(n) for j in range(n)]
        
        for i in range(self.params['n_hidden']):
            coord[i,:] = possible_locs.pop(np.random.randint(len(possible_locs)))
            
        self.params['pairwise_dist'] = np.zeros((self.params['n_hidden'],self.params['n_hidden']), dtype=np.float32)
        for i in range(self.params['n_hidden']):
            for j in range(self.params['n_hidden']):
                self.params['pairwise_dist'][i,j] = np.sqrt((coord[i,0]-coord[j,0])**2 + (coord[i,1]-coord[j,1])**2)
                
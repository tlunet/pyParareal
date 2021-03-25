from integrator import integrator
from solution import solution
from meshtransfer import meshtransfer

import numpy as np
import copy

class timeslice(object):

  def __init__(self, int_fine, int_coarse, tolerance, iter_max, u0coarse = None):
    assert (isinstance(tolerance, float) and tolerance>=0), "Parameter tolerance must be positive or zero"
    assert (isinstance(iter_max, int) and iter_max>=0), "Parameter iter_max must be a positive integer or zero"
    assert isinstance(int_fine, integrator), "Parameter int_fine has to be an object of type integrator"
    assert isinstance(int_coarse, integrator), "Parameter int_coarse has to be an object of type integrator"    
    assert np.isclose( int_fine.tstart, int_coarse.tstart, rtol = 1e-10, atol=1e-12 ), "Values tstart in coarse and fine integrator must be identical"
    assert np.isclose( int_fine.tend, int_coarse.tend, rtol = 1e-10, atol=1e-12 ), "Values tend in coarse and fine integrator must be identical"
    self.int_fine    = int_fine
    self.int_coarse  = int_coarse
    self.tolerance   = tolerance
    self.iter_max    = iter_max
    self.iteration   = 0
    self.coarse_temp = copy.deepcopy(u0coarse)

  def update_fine(self):
    assert hasattr(self, 'sol_start'), "Timeslice object does not have attribute sol_start - may be function set_sol_start was never executed"   
    self.sol_fine = copy.deepcopy(self.sol_start)
    self.int_fine.run(self.sol_fine)

  def update_coarse(self):
    assert hasattr(self, 'sol_start'), "Timeslice object does not have attribute sol_start - may be function set_sol_start was never executed"

    # Copy the
    if (self.coarse_temp is None):
      # if coarse_temp is none, no u0coarse argument was provided and spatial coarsening is not used
      temp     = copy.deepcopy(self.sol_coarse)
    else:
      temp     = copy.deepcopy(self.coarse_temp)
      
    self.meshtransfer.restrict(self.sol_start, temp)
    self.int_coarse.run(temp)
    self.meshtransfer.interpolate(self.sol_coarse, temp)
        
  #
  # SET functions
  #

  def set_sol_start(self, sol):
    assert isinstance(sol, solution), "Parameter sol has to be of type solution"
    self.sol_start = sol
    # For later use, also create the attribute sol_coarse - the values in it will be overwritten when update_coarse is called
    self.sol_coarse = copy.deepcopy(self.sol_start)
    
    # also generate the meshtransfer attribute now
    if not hasattr(self, 'meshtransfer'):
      self.setup_meshtransfer()

  def setup_meshtransfer(self):
      if self.coarse_temp is None:
        # if u0coarse was not provided, no spatial coarsening is used and the number of DoF is the same on both levels: interpolation and restriction become the identity in this case
        self.meshtransfer = meshtransfer(self.sol_start.ndof, self.sol_start.ndof)
      else:
        self.meshtransfer = meshtransfer(self.sol_start.ndof, self.coarse_temp.ndof)
        
  def set_sol_end(self, sol):
    assert isinstance(sol, solution), "Parameter sol has to be of type solution"
    self.sol_end = sol

  def increase_iter(self):
    self.iteration += 1

  def set_residual(self):
    assert hasattr(self, 'sol_fine'), "Timeslice object does not have attribute sol_fine - may be function update_fine was never executed"
    assert hasattr(self, 'sol_end'), "Timeslice object does not have attribute sol_end - it has to be assigned using set_sol_end"
    # compute || F(y_n-1) - y_n ||
    res = self.sol_fine
    res.axpy(-1.0, self.sol_end)
    self.residual = res.norm()
    return self.residual

  #
  # GET functions
  #

  # For linear problems, returns a matrix that corresponds to running the fine method
  def get_fine_update_matrix(self, sol):
    return self.int_fine.get_update_matrix(sol)

  # For linear problems, returns a matrix that corresponds to running the coarse method
  def get_coarse_update_matrix(self, sol):
    if self.coarse_temp is None:
      return self.int_coarse.get_update_matrix(sol)
    else:
      G = self.int_coarse.get_update_matrix(sol)
      # if timeslice is used only to generate a matrix representation of the integrators, the meshtransfer object might not yet exists - if so, generate it
      if not hasattr(self, 'meshtransfer'):
        self.set_sol_start(sol)
        self.setup_meshtransfer()
      return self.meshtransfer.Imat@(G@self.meshtransfer.Rmat)

  def get_tstart(self):
    return self.int_fine.tstart

  def get_tend(self):
    return self.int_fine.tend

  def get_sol_fine(self):
    assert hasattr(self, 'sol_fine'), "Timeslice object does not have attribute sol_fine - may be function update_fine was never executed"
    return self.sol_fine

  def get_sol_coarse(self):
    assert hasattr(self, 'sol_coarse'), "Timeslice object does not have attribute sol_coarse - may be function update_coarse was never executed"
    return self.sol_coarse

  def get_sol_end(self):
    assert hasattr(self, 'sol_end'), "Timeslice object does not have attribute sol_end - may be function set_sol_end was never executed"
    return self.sol_end

  def get_residual(self):
    self.set_residual()
    return self.residual

  #
  # IS functions
  #

  def is_converged(self):
    # update residual
    self.set_residual()
    if ( (self.get_residual()<self.tolerance) or (self.iteration>=self.iter_max) ):
      return True
    else:
      return False

"""
This module gathers basic and general plasma parameters such as the
plasma frequency or Debye length.
"""
__all__ = [
    "mass_density",
    "Alfven_speed",
    "ion_sound_speed",
    "thermal_speed",
    "thermal_pressure",
    "kappa_thermal_speed",
    "Hall_parameter",
    "gyrofrequency",
    "gyroradius",
    "plasma_frequency",
    "Debye_length",
    "Debye_number",
    "inertial_length",
    "magnetic_pressure",
    "magnetic_energy_density",
    "upper_hybrid_frequency",
    "lower_hybrid_frequency",
]

import numbers
import numpy as np
import warnings

from astropy import units as u
from astropy.constants.si import (m_p, m_e, c, mu0, k_B, e, eps0)
from plasmapy import atomic
from plasmapy.utils import PhysicsError
from plasmapy.utils.decorators import (angular_freq_to_hz, check_relativistic, validate_quantities)
from plasmapy.utils.exceptions import PhysicsWarning
from typing import Optional


def _grab_charge(ion, z_mean=None):
    """Utility function to merge two possible inputs for particle charge.

    Parameters
    ----------
    ion : str or `plasmapy.atomic.Particle`
        a string representing a charged particle, or a Particle object.

    z_mean : float
        An optional float describing the average ionization of a particle
        species.

    Returns
    -------
    float
        if `z_mean` was passed, `z_mean`, otherwise, the integer charge
        of the `ion`.

    """
    if z_mean is None:
        # warnings.warn("No z_mean given, defaulting to atomic charge",
        #               PhysicsWarning)
        Z = atomic.integer_charge(ion)
    else:
        # using average ionization provided by user
        Z = z_mean
    return Z


@validate_quantities(density={'can_be_negative': False},
                     validations_on_return={'can_be_negative': False})
def mass_density(density: [u.m ** -3, u.kg / (u.m ** 3)],
                 particle: Optional[str] = None,
                 z_mean: Optional[numbers.Real] = None) -> u.kg / u.m ** 3:
    """Utility function to merge two possible inputs for particle charge.

    Parameters
    ----------
    density : ~astropy.units.Quantity
        Either a particle density (number of particles per unit volume, in units
        of 1/m^3) or a mass density (in units of kg/m^3 or equivalent).

    particle : str, optional
        Representation of the particle species (e.g., `'p'` for protons, `'D+'`
        for deuterium, or `'He-4 +1'` for singly ionized helium-4),
        which defaults to electrons.  If no charge state information is
        provided, then the particles are assumed to be singly charged.

    z_mean : float
        An optional float describing the average ionization of a particle
        species.

    Raises
    ------
    ValueError
        If the `density` has units inconvertible to either a particle density
        or a mass density, or if you pass in a number density without a particle.

    Returns
    -------
    ~astropy.units.Quantity
        The mass density calculated from all the provided sources of information.

    Examples
    -------
    >>> from astropy import units as u
    >>> mass_density(1 * u.m ** -3,'p')
    <Quantity 1.67353284e-27 kg / m3>
    >>> mass_density(4 * u.m ** -3,'D+')
    <Quantity 1.33779786e-26 kg / m3>

    """
    # validate_quantities ensures we have units of u.kg/u.m**3 or 1/u.m**3
    rho = density
    if not rho.unit.is_equivalent(u.kg / u.m ** 3):
        if particle:
            m_i = atomic.particle_mass(particle)
            Z = _grab_charge(particle, z_mean)
            rho = density * m_i + Z * density * m_e
        else:
            raise ValueError(f"If passing a number density, you must pass a "
                             f"particle (not {particle}) to calculate the mass density!")

    return rho


@check_relativistic
@validate_quantities(density={'can_be_negative': False})
def Alfven_speed(B: u.T,
                 density: [u.m ** -3, u.kg / u.m ** 3],
                 ion="p+",
                 z_mean=None) -> u.m / u.s:
    r"""
    Return the Alfvén speed.

    Parameters
    ----------
    B : ~astropy.units.Quantity
        The magnetic field magnitude in units convertible to tesla.

    density : ~astropy.units.Quantity
        Either the ion number density in units convertible to 1 / m**3,
        or the mass density in units convertible to kg / m**3.

    ion : str, optional
        Representation of the ion species (e.g., `'p'` for protons,
        `'D+'` for deuterium, or `'He-4 +1'` for singly ionized
        helium-4), which defaults to protons.  If no charge state
        information is provided, then the ions are assumed to be
        singly charged.

    z_mean : ~astropy.units.Quantity, optional
        The average ionization (arithmetic mean) for a plasma where the
        a macroscopic description is valid. If this quantity is not
        given then the atomic charge state (integer) of the ion
        is used. This is effectively an average Alfven speed for the
        plasma where multiple charge states are present.

    Returns
    -------
    V_A : ~astropy.units.Quantity with units of speed
        The Alfvén speed of the plasma in units of meters per second.

    Raises
    ------
    TypeError
        The magnetic field and density arguments are not instances of
        `~astropy.units.Quantity` and cannot be converted into those.

    ~astropy.units.UnitConversionError
        If the magnetic field or density is not in appropriate units.

    ~plasmapy.utils.RelativityError
        If the Alfven velocity is greater than or equal to the speed of light

    ValueError
        If the density is negative, or the ion mass or charge state
        cannot be found.

    Warns
    -----
    ~plasmapy.utils.RelativityWarning
        If the Alfven velocity exceeds 5% of the speed of light

    ~astropy.units.UnitsWarning
        if units are not provided, SI units are assumed.

    Notes
    -----
    The Alfven speed :math:`V_A` is the typical propagation speed
    of magnetic disturbances in a plasma, and is given by:

    .. math::

        V_A = \frac{B}{\sqrt{\mu_0\rho}}

    where the mass density is :math:`\rho = n_i m_i + n_e m_e`.

    This expression does not account for relativistic effects, and
    loses validity when the resulting speed is a significant fraction
    of the speed of light.

    Examples
    --------
    >>> from astropy import units as u
    >>> from astropy.constants.si import m_p, m_e
    >>> B = 0.014*u.T
    >>> n = 5e19*u.m**-3
    >>> rho = n*(m_p+m_e)
    >>> ion = 'p'
    >>> Alfven_speed(B, n, ion)
    <Quantity 43173.87029559 m / s>
    >>> Alfven_speed(B, rho, ion)
    <Quantity 43173.87029559 m / s>
    >>> Alfven_speed(B, rho, ion).to(u.cm/u.us)
    <Quantity 4.31738703 cm / us>

    """
    rho = mass_density(density, ion, z_mean)

    V_A = (np.abs(B) / np.sqrt(mu0 * rho))
    return V_A


@check_relativistic
@validate_quantities(T_i={'can_be_negative': False,
                          'equivalencies': u.temperature_energy()},
                     T_e={'can_be_negative': False,
                          'equivalencies': u.temperature_energy()},
                     n_e={'can_be_negative': False,
                          'none_shall_pass': True},
                     k={'can_be_negative': False,
                        'none_shall_pass': True})
def ion_sound_speed(T_e: u.K,
                    T_i: u.K,
                    n_e: u.m ** -3 = None,
                    k: u.m ** -1 = None,
                    gamma_e=1,
                    gamma_i=3,
                    ion='p+',
                    z_mean=None) -> u.m / u.s:
    r"""
    Return the ion sound speed for an electron-ion plasma.

    Parameters
    ----------
    T_e : ~astropy.units.Quantity
        Electron temperature in units of temperature or energy per
        particle. If this is not given, then the electron temperature
        is assumed to be zero.

    T_i : ~astropy.units.Quantity
        Ion temperature in units of temperature or energy per
        particle.  If this is not given, then the ion temperature is
        assumed to be zero.
        
    n_e : ~astropy.units.Quantity
        Electron number density. If this is not given, then ion_sound_speed 
        will be approximated in the non-dispersive limit 
        (:math:`k^2 \lambda_{D}^2` will be assumed zero). If n_e is given, 
        a value for k must also be given.
        
    k : ~astropy.units.Quantity
        Wavenumber (in units of inverse length, e.g. per meter). If this 
        is not given, then ion_sound_speed will be approximated in the 
        non-dispersive limit (:math:`k^2 \lambda_{D}^2` will be assumed zero). 
        If k is given, a value for n_e must also be given.

    gamma_e : float or int
        The adiabatic index for electrons, which defaults to 1.  This
        value assumes that the electrons are able to equalize their
        temperature rapidly enough that the electrons are effectively
        isothermal.

    gamma_i : float or int
        The adiabatic index for ions, which defaults to 3.  This value
        assumes that ion motion has only one degree of freedom, namely
        along magnetic field lines.

    ion : str, optional
        Representation of the ion species (e.g., `'p'` for protons,
        `'D+'` for deuterium, or 'He-4 +1' for singly ionized
        helium-4), which defaults to protons.  If no charge state
        information is provided, then the ions are assumed to be
        singly charged.

    z_mean : ~astropy.units.Quantity, optional
        The average ionization (arithmetic mean) for a plasma where the
        a macroscopic description is valid. If this quantity is not
        given then the atomic charge state (integer) of the ion
        is used. This is effectively an average ion sound speed for the
        plasma where multiple charge states are present.

    Returns
    -------
    V_S : ~astropy.units.Quantity
        The ion sound speed in units of meters per second.

    Raises
    ------
    TypeError
        If any of the arguments are not entered as keyword arguments
        or are of an incorrect type.

    ValueError
        If the ion mass, adiabatic index, or temperature are invalid.

    ~plasmapy.utils.PhysicsError
        If an adiabatic index is less than one.

    ~astropy.units.UnitConversionError
        If the temperature, electron number density, or wavenumber 
        is in incorrect units.

    Warns
    -----
    RelativityWarning
        If the ion sound speed exceeds 5% of the speed of light.

    ~astropy.units.UnitsWarning
        If units are not provided, SI units are assumed.
        
    PhysicsWarning
        If only one of (k, n_e) is given, the non-dispersive limit 
        is assumed.

    Notes
    -----
    The ion sound speed :math:`V_S` is given by

    .. math::

        V_S = \sqrt{\frac{\gamma_e Z k_B T_e + \gamma_i k_B T_i}{m_i (1 + k^2 \lambda_{D}^2)}}

    where :math:`\gamma_e` and :math:`\gamma_i` are the electron and
    ion adiabatic indices, :math:`k_B` is the Boltzmann constant,
    :math:`T_e` and :math:`T_i` are the electron and ion temperatures,
    :math:`Z` is the charge state of the ion, :math:`m_i` is the
    ion mass, :math:`\lambda_{D}` is the Debye length, and :math:`k` is the 
    wavenumber.
    
    In the non-dispersive limit (:math:`k^2 \lambda_{D}^2` is small) the 
    equation for :math:`V_S` is approximated (the denominator reduces 
    to :math:`m_i`).

    When the electron temperature is much greater than the ion
    temperature, the ion sound velocity reduces to
    :math:`\sqrt{\gamma_e k_B T_e / m_i}`. Ion acoustic waves can
    therefore occur even when the ion temperature is zero.

    Example
    -------
    >>> from astropy import units as u
    >>> n = 5e19*u.m**-3
    >>> k_1 = 3e1*u.m**-1
    >>> k_2 = 3e7*u.m**-1
    >>> ion_sound_speed(T_e=5e6*u.K, T_i=0*u.K, ion='p', gamma_e=1, gamma_i=3)
    <Quantity 203155.0764042 m / s>
    >>> ion_sound_speed(T_e=5e6*u.K, T_i=0*u.K, n_e=n, k=k_1, ion='p', gamma_e=1, gamma_i=3)
    <Quantity 203155.03286794 m / s>
    >>> ion_sound_speed(T_e=5e6*u.K, T_i=0*u.K, n_e=n, k=k_2, ion='p', gamma_e=1, gamma_i=3)
    <Quantity 310.31329069 m / s>
    >>> ion_sound_speed(T_e=5e6*u.K, T_i=0*u.K, n_e=n, k=k_1)
    <Quantity 203155.03286794 m / s>
    >>> ion_sound_speed(T_e=500*u.eV, T_i=200*u.eV, n_e=n, k=k_1, ion='D+')
    <Quantity 229585.96150738 m / s>

    """
    
    m_i = atomic.particle_mass(ion)
    Z = _grab_charge(ion, z_mean)

    for gamma, particles in zip([gamma_e, gamma_i], ["electrons", "ions"]):
        if not isinstance(gamma, (numbers.Real, numbers.Integral)):
            raise TypeError(f"The adiabatic index gamma for {particles} must be "
                            "a float or int")
        if gamma < 1:
            raise PhysicsError(f"The adiabatic index for {particles} must be between "
                               f"one and infinity")
    
    # Assume non-dispersive limit if values for n_e (or k) are not specified
    klD2 = 0.0
    if (n_e is None) ^ (k is None):
        warnings.warn("The non-dispersive limit has been assumed for "
                      "this calculation. To prevent this, values must "
                      "be specified for both n_e and k.", PhysicsWarning)
    elif n_e is not None and k is not None:
        lambda_D = Debye_length(T_e, n_e)
        klD2 = (k * lambda_D) ** 2

    try:
        V_S_squared = (gamma_e * Z * k_B * T_e + gamma_i * k_B * T_i) / (m_i * (1 + klD2))
        V_S = np.sqrt(V_S_squared).to(u.m / u.s)
    except Exception:
        raise ValueError("Unable to find ion sound speed.")

    return V_S


@check_relativistic
@validate_quantities(T={'can_be_negative': False,
                        'equivalencies': u.temperature_energy()},
                     mass={'can_be_negative': False, 'can_be_nan': True})
@atomic.particle_input
def thermal_speed(T: u.K,
                  particle: atomic.Particle = "e-",
                  method="most_probable",
                  mass: u.kg = np.nan * u.kg) -> u.m / u.s:
    r"""
    Return the most probable speed for a particle within a Maxwellian
    distribution.

    Parameters
    ----------
    T : ~astropy.units.Quantity
        The particle temperature in either kelvin or energy per particle

    particle : str, optional
        Representation of the particle species (e.g., `'p'` for protons, `'D+'`
        for deuterium, or `'He-4 +1'` for singly ionized helium-4),
        which defaults to electrons.  If no charge state information is
        provided, then the particles are assumed to be singly charged.

    method : str, optional
        Method to be used for calculating the thermal speed. Options are
        `'most_probable'` (default), `'rms'`, and `'mean_magnitude'`.

    mass : ~astropy.units.Quantity
        The particle's mass override. Defaults to NaN and if so, doesn't do
        anything, but if set, overrides mass acquired from `particle`. Useful
        with relative velocities of particles.

    Returns
    -------
    V : ~astropy.units.Quantity
        particle thermal speed

    Raises
    ------
    TypeError
        The particle temperature is not a ~astropy.units.Quantity

    ~astropy.units.UnitConversionError
        If the particle temperature is not in units of temperature or
        energy per particle

    ValueError
        The particle temperature is invalid or particle cannot be used to
        identify an isotope or particle

    Warns
    -----
    RelativityWarning
        If the ion sound speed exceeds 5% of the speed of light, or

    ~astropy.units.UnitsWarning
        If units are not provided, SI units are assumed.

    Notes
    -----
    The particle thermal speed is given by:

    .. math::
        V_{th,i} = \sqrt{\frac{2 k_B T_i}{m_i}}

    This function yields the most probable speed within a distribution
    function.  However, the definition of thermal velocity varies by
    the square root of two depending on whether or not this velocity
    absorbs that factor in the expression for a Maxwellian
    distribution.  In particular, the expression given in the NRL
    Plasma Formulary [1] is a square root of two smaller than the
    result from this function.

    Examples
    --------
    >>> from astropy import units as u
    >>> thermal_speed(5*u.eV, 'p')
    <Quantity 30949.69018286 m / s>
    >>> thermal_speed(1e6*u.K, particle='p')
    <Quantity 128486.55193256 m / s>
    >>> thermal_speed(5*u.eV)
    <Quantity 1326205.12123959 m / s>
    >>> thermal_speed(1e6*u.K)
    <Quantity 5505693.98842538 m / s>
    >>> thermal_speed(1e6*u.K, method="rms")
    <Quantity 6743070.47577549 m / s>
    >>> thermal_speed(1e6*u.K, method="mean_magnitude")
    <Quantity 6212510.3969422 m / s>

    """
    m = mass if np.isfinite(mass) else atomic.particle_mass(particle)

    # different methods, as per https://en.wikipedia.org/wiki/Thermal_velocity
    if method == "most_probable":
        V = (np.sqrt(2 * k_B * T / m))
    elif method == "rms":
        V = (np.sqrt(3 * k_B * T / m))
    elif method == "mean_magnitude":
        V = (np.sqrt(8 * k_B * T / (m * np.pi)))
    else:
        raise ValueError("Method {method} not supported in thermal_speed")

    return V


@validate_quantities(T={'can_be_negative': False,
                        'equivalencies': u.temperature_energy()},
                     n={'can_be_negative': False})
def thermal_pressure(T: u.K, n: u.m ** -3) -> u.Pa:
    r"""
    Return the thermal pressure for a Maxwellian distribution.

    Parameters
    ----------
    T : ~astropy.units.Quantity
        The particle temperature in either kelvin or energy per particle

    n : ~astropy.units.Quantity
        The particle number density in units convertible to m**-3.

    Examples
    --------
    >>> import astropy.units as u
    >>> thermal_pressure(1*u.eV, 1e20/u.m**3)
    <Quantity 16.02176621 Pa>
    >>> thermal_pressure(10*u.eV, 1e20/u.m**3)
    <Quantity 160.21766208 Pa>

    Returns
    -------
    p_th : ~astropy.units.Quantity
        Thermal pressure.

    Raises
    ------
    TypeError
        The temperature or number density is not a `~astropy.units.Quantity`.

    ~astropy.units.UnitConversionError
        If the particle temperature is not in units of temperature or
        energy per particle.

    Notes
    -----
    The thermal pressure is given by:

    .. math::
        T_{th} = nk_{B}T
    """

    return n * k_B * T


@check_relativistic
@validate_quantities(T={'can_be_negative': False,
                        'equivalencies': u.temperature_energy()})
def kappa_thermal_speed(T: u.K, kappa, particle="e-", method="most_probable") -> u.m / u.s:
    r"""Return the most probable speed for a particle within a Kappa
    distribution.

    Parameters
    ----------
    T : ~astropy.units.Quantity
        The particle temperature in either kelvin or energy per particle

    kappa: float
        The kappa parameter is a dimensionless number which sets the slope
        of the energy spectrum of suprathermal particles forming the tail
        of the Kappa velocity distribution function. Kappa must be greater
        than 3/2.

    particle : str, optional
        Representation of the particle species (e.g., 'p' for protons, 'D+'
        for deuterium, or 'He-4 +1' for singly ionized helium-4),
        which defaults to electrons.  If no charge state information is
        provided, then the particles are assumed to be singly charged.

    method : str, optional
        Method to be used for calculating the thermal speed. Options are
        'most_probable' (default), 'rms', and 'mean_magnitude'.

    Returns
    -------
    V : ~astropy.units.Quantity
        Particle thermal speed

    Raises
    ------
    TypeError
        The particle temperature is not a ~astropy.units.Quantity.

    astropy.units.UnitConversionError
        If the particle temperature is not in units of temperature or
        energy per particle.

    ValueError
        The particle temperature is invalid or particle cannot be used to
        identify an isotope or particle.

    Warns
    -----
    RelativityWarning
        If the particle thermal speed exceeds 5% of the speed of light, or

    ~astropy.units.UnitsWarning
        If units are not provided, SI units are assumed.

    Notes
    -----
    The particle thermal speed is given by:

    .. math::
        V_{th,i} = \sqrt{(2 \kappa - 3)\frac{2 k_B T_i}{\kappa m_i}}

    For more discussion on the mean_magnitude calculation method, see [1]_.


    Examples
    --------
    >>> from astropy import units as u
    >>> kappa_thermal_speed(5*u.eV, 4, 'p') # defaults to most probable
    <Quantity 24467.87846359 m / s>
    >>> kappa_thermal_speed(5*u.eV, 4, 'p', 'rms')
    <Quantity 37905.47432261 m / s>
    >>> kappa_thermal_speed(5*u.eV, 4, 'p', 'mean_magnitude')
    <Quantity 34922.9856304 m / s>

    References
    ----------
    .. [1] PlasmaPy Issue #186, https://github.com/PlasmaPy/PlasmaPy/issues/186

    See Also
    --------
    plasmapy.formulary.kappa_thermal_speed
    plasmapy.formulary.kappa_velocity_1D
    """
    # Checking thermal units
    if kappa <= 3 / 2:
        raise ValueError(f"Must have kappa > 3/2, instead of {kappa}, for "
                         "kappa distribution function to be valid.")
    # different methods, as per https://en.wikipedia.org/wiki/Thermal_velocity
    vTh = thermal_speed(T=T,
                        particle=particle,
                        method=method)

    if method == "most_probable":
        # thermal velocity of Kappa distribution function is just Maxwellian
        # thermal speed modulated by the following factor.
        # This is only true for "most probable" case. RMS and mean
        # magnitude velocities are same as Maxwellian.
        coeff = np.sqrt((kappa - 3 / 2) / kappa)
    else:
        coeff = 1

    return vTh * coeff


@validate_quantities(n={'can_be_negative': False},
                     T={'can_be_negative': False,
                        'equivalencies': u.temperature_energy()})
def Hall_parameter(n: u.m ** -3,
                   T: u.K,
                   B: u.T,
                   ion_particle,
                   particle='e-',
                   coulomb_log=None,
                   V=None,
                   coulomb_log_method="classical"):
    r"""Calculate the ratio between the particle gyrofrequency and the
    particle-ion particle collision rate.

    All parameters apply to `particle`.

    Parameters
    ----------
    n : ~astropy.units.quantity.Quantity
        The density of particle s
    T : ~astropy.units.quantity.Quantity
        The temperature of particles
    B : ~astropy.units.quantity.Quantity
        The magnetic field
    ion_particle : str
        String signifying the type of ion.
    particle : str, optional
        String signifying the type of particles. Defaults to electrons.
    coulomb_log : float, optional
        Preset value for the Coulomb logarithm. Used mostly for testing purposes.
    V : ~astropy.units.quantity.Quantity
        The relative velocity between `particle` and ion particles.
    coulomb_log_method : str, optional
        Method used for Coulomb logarithm calculation. Refer to its documentation.

    See Also
    --------
    plasmapy.formulary.parameters.gyrofrequency
    plasmapy.formulary.parameters.fundamental_electron_collision_freq
    plasmapy.formulary.collisions.Coulomb_logarithm

    Returns
    -------
    astropy.units.quantity.Quantity

    Examples
    --------
    >>> from astropy import units as u
    >>> Hall_parameter(1e10 * u.m**-3, 2.8e3 * u.eV, 2.3 * u.T, 'He-4 +1')
    <Quantity 7.26446755e+16>
    >>> Hall_parameter(1e10 * u.m**-3, 5.8e3 * u.eV, 2.3 * u.T, 'He-4 +1')
    <Quantity 2.11158408e+17>

    """
    from plasmapy.formulary.collisions import (fundamental_ion_collision_freq,
                                               fundamental_electron_collision_freq)
    gyro_frequency = gyrofrequency(B, particle)
    gyro_frequency = gyro_frequency / u.radian
    if atomic.Particle(particle).particle == 'e-':
        coll_rate = fundamental_electron_collision_freq(T,
                                                        n,
                                                        ion_particle,
                                                        coulomb_log,
                                                        V,
                                                        coulomb_log_method=coulomb_log_method)
    else:
        coll_rate = fundamental_ion_collision_freq(T, n, ion_particle, coulomb_log, V)
    return gyro_frequency / coll_rate


@validate_quantities(validations_on_return={'units': [u.rad / u.s, u.Hz],
                                            'equivalencies': [(u.cy / u.s, u.Hz)]})
@angular_freq_to_hz
def gyrofrequency(B: u.T, particle='e-', signed=False, Z=None) -> u.rad / u.s:
    r"""Calculate the particle gyrofrequency in units of radians per second.

    Parameters
    ----------
    B : ~astropy.units.Quantity
        The magnetic field magnitude in units convertible to tesla.

    particle : str, optional
        Representation of the particle species (e.g., 'p' for protons, 'D+'
        for deuterium, or 'He-4 +1' for singly ionized helium-4),
        which defaults to electrons.  If no charge state information is
        provided, then the particles are assumed to be singly charged.

    signed : bool, optional
        The gyrofrequency can be defined as signed (negative for electron,
        positive for ion). Default is `False` (unsigned, i.e. always
        positive).

    Z : float or ~astropy.units.Quantity, optional
        The average ionization (arithmetic mean) for a plasma where the
        a macroscopic description is valid. If this quantity is not
        given then the atomic charge state (integer) of the ion
        is used. This is effectively an average gyrofrequency for the
        plasma where multiple charge states are present, and should
        not be interpreted as the gyrofrequency for any single particle.
        If not provided, it defaults to the integer charge of the `particle`.

    Returns
    -------
    omega_c : ~astropy.units.Quantity
        The particle gyrofrequency in units of radians per second

    Raises
    ------
    TypeError
        If the magnetic field is not a `Quantity` or particle is not of an
        appropriate type

    ValueError
        If the magnetic field contains invalid values or particle cannot be
        used to identify an particle or isotope

    Warns
    -----
    ~astropy.units.UnitsWarning
        If units are not provided, SI units are assumed

    Notes
    -----
    The particle gyrofrequency is the angular frequency of particle gyration
    around magnetic field lines and is given by:

    .. math::
        \omega_{ci} = \frac{Z e B}{m_i}

    The particle gyrofrequency is also known as the particle cyclotron
    frequency or the particle Larmor frequency.

    The recommended way to convert from angular frequency to frequency
    is to use an equivalency between cycles per second and Hertz, as
    Astropy's `dimensionles_angles` equivalency does not account for
    the factor of 2*pi needed during this conversion.  The
    `dimensionless_angles` equivalency is appropriate when dividing a
    velocity by an angular frequency to get a length scale.

    Examples
    --------
    >>> from astropy import units as u
    >>> gyrofrequency(0.1*u.T)
    <Quantity 1.75882002e+10 rad / s>
    >>> gyrofrequency(0.1*u.T, to_hz=True)
    <Quantity 2.79924901e+09 Hz>
    >>> gyrofrequency(0.1*u.T, signed=True)
    <Quantity -1.75882002e+10 rad / s>
    >>> gyrofrequency(0.01*u.T, 'p')
    <Quantity 957883.32241481 rad / s>
    >>> gyrofrequency(0.01*u.T, 'p', signed=True)
    <Quantity 957883.32241481 rad / s>
    >>> gyrofrequency(0.01*u.T, particle='T+')
    <Quantity 319964.54975911 rad / s>
    >>> gyrofrequency(0.01*u.T, particle='T+', to_hz=True)
    <Quantity 50923.93970833 Hz>
    >>> omega_ce = gyrofrequency(0.1*u.T)
    >>> print(omega_ce)
    17588200236.02124 rad / s
    >>> f_ce = omega_ce.to(u.Hz, equivalencies=[(u.cy/u.s, u.Hz)])
    >>> print(f_ce)
    2799249007.6528206 Hz

    """
    m_i = atomic.particle_mass(particle)
    Z = _grab_charge(particle, Z)
    if not signed:
        Z = abs(Z)

    omega_ci = u.rad * (Z * e * np.abs(B) / m_i).to(1 / u.s)

    return omega_ci


@validate_quantities(Vperp={'can_be_nan': True},
                     T_i={'can_be_nan': True,
                          'equivalencies': u.temperature_energy()},
                     validations_on_return={'equivalencies': u.dimensionless_angles()})
def gyroradius(B: u.T,
               particle='e-',
               *,
               Vperp: u.m / u.s = np.nan * u.m / u.s,
               T_i: u.K = np.nan * u.K) -> u.m:
    r"""Return the particle gyroradius.

    Parameters
    ----------
    B : ~astropy.units.Quantity
        The magnetic field magnitude in units convertible to tesla.

    particle : str, optional
        Representation of the particle species (e.g., `'p'` for protons, `'D+'`
        for deuterium, or `'He-4 +1'` for singly ionized helium-4),
        which defaults to electrons.  If no charge state information is
        provided, then the particles are assumed to be singly charged.

    Vperp : ~astropy.units.Quantity, optional
        The component of particle velocity that is perpendicular to the
        magnetic field in units convertible to meters per second.
        Must be input as a keyword argument.

    T_i : ~astropy.units.Quantity, optional
        The particle temperature in units convertible to kelvin.
        Must be input as a keyword argument.

    Returns
    -------
    r_Li : ~astropy.units.Quantity
        The particle gyroradius in units of meters.  This
        ~astropy.units.Quantity will be based on either the
        perpendicular component of particle velocity as inputted, or
        the most probable speed for an particle within a Maxwellian
        distribution for the particle temperature.

    Raises
    ------
    TypeError
        The arguments are of an incorrect type

    ~astropy.units.UnitConversionError
        The arguments do not have appropriate units

    ValueError
        If any argument contains invalid values

    Warns
    -----
    ~astropy.units.UnitsWarning
        If units are not provided, SI units are assumed

    Notes
    -----
    One but not both of `Vperp` and `T_i` must be inputted.

    If any of `B`, `Vperp`, or `T_i` is a number rather than a
    `~astropy.units.Quantity`, then SI units will be assumed and a
    warning will be raised.

    The particle gyroradius is also known as the particle Larmor
    radius and is given by

    .. math::
        r_{Li} = \frac{V_{\perp}}{omega_{ci}}

    where :math:`V_{\perp}` is the component of particle velocity that is
    perpendicular to the magnetic field and :math:`\omega_{ci}` is the
    particle gyrofrequency.  If a temperature is provided, then
    :math:`V_\perp` will be the most probable thermal velocity of an
    particle at that temperature.

    Examples
    --------
    >>> from astropy import units as u
    >>> gyroradius(0.2*u.T,particle='p+',T_i=1e5*u.K)
    <Quantity 0.00212087 m>
    >>> gyroradius(0.2*u.T,particle='p+',T_i=1e5*u.K)
    <Quantity 0.00212087 m>
    >>> gyroradius(5*u.uG,particle='alpha',T_i=1*u.eV)
    <Quantity 288002.38837768 m>
    >>> gyroradius(400*u.G,particle='Fe+++',Vperp=1e7*u.m/u.s)
    <Quantity 48.23129811 m>
    >>> gyroradius(B=0.01*u.T,T_i=1e6*u.K)
    <Quantity 0.00313033 m>
    >>> gyroradius(B=0.01*u.T,Vperp=1e6*u.m/u.s)
    <Quantity 0.00056856 m>
    >>> gyroradius(0.2*u.T,T_i=1e5*u.K)
    <Quantity 4.94949252e-05 m>
    >>> gyroradius(5*u.uG,T_i=1*u.eV)
    <Quantity 6744.2598183 m>
    >>> gyroradius(400*u.G,Vperp=1e7*u.m/u.s)
    <Quantity 0.00142141 m>

    """

    isfinite_Ti = np.isfinite(T_i)
    isfinite_Vperp = np.isfinite(Vperp)

    # check 1: ensure either Vperp or T_i invalid, keeping in mind that
    # the underlying values of the astropy quantity may be numpy arrays
    if np.any(np.logical_not(np.logical_xor(isfinite_Vperp, isfinite_Ti))):
        raise ValueError("Must give Vperp or T_i, but not both, as arguments to gyroradius")

    # check 2: get Vperp as the thermal speed if is not already a valid input
    if np.isscalar(Vperp.value) and np.isscalar(T_i.value):  # both T_i and Vperp are scalars
        # we know exactly one of them is nan from check 1
        if isfinite_Ti:
            # T_i is valid, so use it to determine Vperp
            Vperp = thermal_speed(T_i, particle=particle)
        # else: Vperp is alread valid, do nothing
    elif np.isscalar(Vperp.value):  # only T_i is an array
        # this means either Vperp must be nan, or T_i must be array of all nan,
        # or else we couldn't have gotten through check 1
        if isfinite_Vperp:
            # Vperp is valid, T_i is a vector that is all nan
            # uh...
            Vperp = np.repeat(Vperp, len(T_i))
        else:
            # normal case where Vperp is scalar nan and T_i is valid array
            Vperp = thermal_speed(T_i, particle=particle)
    elif np.isscalar(T_i.value):  # only Vperp is an array
        # this means either T_i must be nan, or V_perp must be array of all nan,
        # or else we couldn't have gotten through check 1
        if isfinite_Ti:
            # T_i is valid, V_perp is an array of all nan
            # uh...
            Vperp = thermal_speed(np.repeat(T_i, len(Vperp)), particle=particle)
        # else: normal case where T_i is scalar nan and Vperp is already a valid array
        # so, do nothing
    else:  # both T_i and Vperp are arrays
        # we know all the elementwise combinations have one nan and one finite, due to check 1
        # use the valid Vperps, and replace the others with those calculated from T_i
        Vperp = Vperp.copy()  # avoid changing Vperp's value outside function
        Vperp[isfinite_Ti] = thermal_speed(T_i[isfinite_Ti], particle=particle)

    omega_ci = gyrofrequency(B, particle)

    r_Li = np.abs(Vperp) / omega_ci

    return r_Li


@validate_quantities(n={'can_be_negative': False},
                     validations_on_return={'units': [u.rad / u.s, u.Hz],
                                            'equivalencies': [(u.cy / u.s, u.Hz)]})
@angular_freq_to_hz
def plasma_frequency(n: u.m**-3, particle='e-', z_mean=None) -> u.rad / u.s:
    r"""Calculate the particle plasma frequency.

    Parameters
    ----------
    n : ~astropy.units.Quantity
        Particle number density in units convertible to per cubic meter

    particle : str, optional
        Representation of the particle species (e.g., 'p' for protons, 'D+'
        for deuterium, or 'He-4 +1' for singly ionized helium-4),
        which defaults to electrons.  If no charge state information is
        provided, then the particles are assumed to be singly charged.

    z_mean : ~astropy.units.Quantity, optional
        The average ionization (arithmetic mean) for a plasma where the
        a macroscopic description is valid. If this quantity is not
        given then the atomic charge state (`int`) of the ion
        is used. This is effectively an average plasma frequency for the
        plasma where multiple charge states are present.

    Returns
    -------
    omega_p : ~astropy.units.Quantity
        The particle plasma frequency in radians per second.

    Raises
    ------
    TypeError
        If n_i is not a `~astropy.units.Quantity` or particle is not of
        an appropriate type.

    UnitConversionError
        If `n_i` is not in correct units

    ValueError
        If `n_i` contains invalid values or particle cannot be used to
        identify an particle or isotope.

    Warns
    -----
    ~astropy.units.UnitsWarning
        If units are not provided, SI units are assumed

    Notes
    -----
    The particle plasma frequency is

    .. math::
        \omega_{pi} = Z e \sqrt{\frac{n_i}{\epsilon_0 m_i}}

    At present, astropy.units does not allow direct conversions from
    radians/second for angular frequency to 1/second or Hz for
    frequency.  The dimensionless_angles equivalency allows that
    conversion, but does not account for the factor of 2*pi. The
    alternatives are to convert to cycle/second or to do the
    conversion manually, as shown in the examples.

    Example
    -------
    >>> from astropy import units as u
    >>> plasma_frequency(1e19*u.m**-3, particle='p')
    <Quantity 4.16329453e+09 rad / s>
    >>> plasma_frequency(1e19*u.m**-3, particle='p', to_hz=True)
    <Quantity 6.62608904e+08 Hz>
    >>> plasma_frequency(1e19*u.m**-3, particle='D+')
    <Quantity 2.94462452e+09 rad / s>
    >>> plasma_frequency(1e19*u.m**-3)
    <Quantity 1.78398636e+11 rad / s>
    >>> plasma_frequency(1e19*u.m**-3, to_hz=True)
    <Quantity 2.83930248e+10 Hz>

    """

    try:
        m = atomic.particle_mass(particle)
        if z_mean is None:
            # warnings.warn("No z_mean given, defaulting to atomic charge",
            #               PhysicsWarning)
            try:
                Z = atomic.integer_charge(particle)
            except Exception:
                Z = 1
        else:
            # using user provided average ionization
            Z = z_mean
        Z = np.abs(Z)
        # TODO REPLACE WITH Z = np.abs(_grab_charge(particle, z_mean)), some bugs atm
    except Exception:
        raise ValueError(f"Invalid particle, {particle}, in "
                         "plasma_frequency.")

    omega_p = u.rad * Z * e * np.sqrt(n / (eps0 * m))

    return omega_p.si


@validate_quantities(T_e={'can_be_negative': False,
                          'equivalencies': u.temperature_energy()},
                     n_e={'can_be_negative': False})
def Debye_length(T_e: u.K, n_e: u.m ** -3) -> u.m:
    r"""Calculate the characteristic decay length for electric fields,
     due to charge screening.

    Parameters
    ----------
    T_e: ~astropy.units.Quantity
        Electron temperature

    n_e: ~astropy.units.Quantity
        Electron number density

    Returns
    -------
    lambda_D : ~astropy.units.Quantity
        The Debye length in meters

    Raises
    ------
    TypeError
        If either argument is not a `~astropy.units.Quantity`

    ~astropy.units.UnitConversionError
        If either argument is in incorrect units

    ValueError
        If either argument contains invalid values

    Warns
    -----
    ~astropy.units.UnitsWarning
        If units are not provided, SI units are assumed

    Notes
    -----
    The Debye length is the exponential scale length for charge
    screening and is given by

    .. math::
        \lambda_D = \sqrt{\frac{\epsilon_0 k_b T_e}{n_e e^2}}

    for an electron plasma with nearly stationary ions.

    The electrical potential will drop by a factor of 1/e every Debye
    length.

    Plasmas will generally be quasineutral on length scales significantly
    larger than the Debye length.

    See Also
    --------
    Debye_number

    Example
    -------
    >>> from astropy import units as u
    >>> Debye_length(5e6*u.K, 5e15*u.m**-3)
    <Quantity 0.00218226 m>

    """
    lambda_D = np.sqrt(eps0 * k_B * T_e / (n_e * e ** 2))
    return lambda_D


@validate_quantities(T_e={'can_be_negative': False,
                          'equivalencies': u.temperature_energy()},
                     n_e={'can_be_negative': False})
def Debye_number(T_e: u.K, n_e: u.m ** -3) -> u.dimensionless_unscaled:
    r"""Return the number of electrons within a sphere with a radius
    of the Debye length.

    Parameters
    ----------
    T_e : ~astropy.units.Quantity
        Electron temperature

    n_e : ~astropy.units.Quantity
        Electron number density

    Raises
    ------
    TypeError
        If either argument is not a `~astropy.units.Quantity`

    astropy.units.UnitConversionError
        If either argument is in incorrect units

    ValueError
        If either argument contains invalid values

    Warns
    -----
    ~astropy.units.UnitsWarning
        If units are not provided, SI units are assumed

    Returns
    -------
    N_D : ~astropy.units.Quantity
        Number of electrons within a sphere with a radius of the Debye length

    Notes
    -----
    The Debye number is the number of electrons contained within a sphere with
    a radius of a Debye length and is given by

    .. math::
        N_D = \frac{4\pi}{3}n_e\lambda_D^3

    The Debye number is also known as the plasma parameter.

    Collective behavior requires a Debye number significantly larger than one.

    See Also
    --------
    Debye_length

    Example
    -------
    >>> from astropy import units as u
    >>> Debye_number(5e6*u.K, 5e9*u.cm**-3)
    <Quantity 2.17658302e+08>

    """

    lambda_D = Debye_length(T_e, n_e)
    N_D = (4 / 3) * np.pi * n_e * lambda_D ** 3

    return N_D


@validate_quantities(n={'can_be_negative': False},
                     validations_on_return={'equivalencies': u.dimensionless_angles()})
@atomic.particle_input(require='charged')
def inertial_length(n: u.m ** -3, particle: atomic.Particle) -> u.m:
    r"""
    Calculate a charged particle's inertial length.

    Parameters
    ----------
    n : ~astropy.units.Quantity
        Particle number density in units convertible to m ** -3.

    particle : str, optional
        Representation of the particle species (e.g., 'p+' for protons,
        'D+' for deuterium, or 'He-4 +1' for singly ionized helium-4).

    Returns
    -------
    d : ~astropy.units.Quantity
        The particle's inertial length in meters.

    Raises
    ------
    TypeError
        If n not a `~astropy.units.Quantity` or particle is not a string.

    ~astropy.units.UnitConversionError
        If n is not in units of a number density.

    ValueError
        The particle density does not have an appropriate value.

    Warns
    -----
    ~astropy.units.UnitsWarning
        If units are not provided and SI units are assumed.

    Notes
    -----
    The inertial length of a particle of species :math:`s` is given by

    .. math::
        d = \frac{c}{\omega_{ps}}

    The inertial length is the characteristic length scale for a
    particle to be accelerated in a plasma.  The Hall effect becomes
    important on length scales shorter than the ion inertial length.

    The inertial length is also known as the skin depth.

    Example
    -------
    >>> from astropy import units as u
    >>> inertial_length(5 * u.m ** -3, 'He+')
    <Quantity 2.02985802e+08 m>
    >>> inertial_length(5 * u.m ** -3, 'e-')
    <Quantity 2376534.75601976 m>

    """
    omega_p = plasma_frequency(n, particle=particle)

    return c / omega_p


@validate_quantities
def magnetic_pressure(B: u.T) -> u.Pa:
    r"""
    Calculate the magnetic pressure.

    Parameters
    ----------
    B : ~astropy.units.Quantity
        The magnetic field in units convertible to tesla.

    Returns
    -------
    p_B : ~astropy.units.Quantity
        The magnetic pressure in units in pascals (newtons per square meter).

    Raises
    ------
    TypeError
        If the input is not a `~astropy.units.Quantity`.

    UnitConversionError
        If the input is not in units convertible to tesla.

    ValueError
        If the magnetic field strength is not a real number between
        +/- infinity.

    Warns
    -----
    ~astropy.units.UnitsWarning
        If units are not provided, SI units are assumed

    Notes
    -----
    The magnetic pressure is given by:

    .. math::
        p_B = \frac{B^2}{2 \mu_0}

    The motivation behind having two separate functions for magnetic
    pressure and magnetic energy density is that it allows greater
    insight into the physics that are being considered by the user and
    thus more readable code.

    See Also
    --------
    magnetic_energy_density : returns an equivalent `~astropy.units.Quantity`,
        except in units of joules per cubic meter.

    Example
    -------
    >>> from astropy import units as u
    >>> magnetic_pressure(0.1*u.T).to(u.Pa)
    <Quantity 3978.8735773 Pa>

    """
    return (B ** 2) / (2 * mu0)


@validate_quantities
def magnetic_energy_density(B: u.T) -> u.J / u.m ** 3:
    r"""
    Calculate the magnetic energy density.

    Parameters
    ----------
    B : ~astropy.units.Quantity
        The magnetic field in units convertible to tesla.

    Returns
    -------
    E_B : ~astropy.units.Quantity
        The magnetic energy density in units of joules per cubic meter.

    Raises
    ------
    TypeError
        If the input is not a Quantity.

    ~astropy.units.UnitConversionError
        If the input is not in units convertible to tesla.

    ValueError
        If the magnetic field strength does not have an appropriate.
        value.

    Warns
    -----
    ~astropy.units.UnitsWarning
        If units are not provided, SI units are assumed

    Notes
    -----
    The magnetic energy density is given by:

    .. math::
        E_B = \frac{B^2}{2 \mu_0}

    The motivation behind having two separate functions for magnetic
    pressure and magnetic energy density is that it allows greater
    insight into the physics that are being considered by the user and
    thus more readable code.

    See Also
    --------
    magnetic_pressure : Returns an equivalent Quantity, except in units
        of pascals.

    Example
    -------
    >>> from astropy import units as u
    >>> magnetic_energy_density(0.1*u.T)
    <Quantity 3978.8735773 J / m3>

    """
    return magnetic_pressure(B)


@validate_quantities(n_e={'can_be_negative': False},
                     validations_on_return={'units': [u.rad / u.s, u.Hz],
                                            'equivalencies': [(u.cy / u.s, u.Hz)]})
@angular_freq_to_hz
def upper_hybrid_frequency(B: u.T, n_e: u.m ** -3) -> u.rad / u.s:
    r"""
    Return the upper hybrid frequency.

    Parameters
    ----------
    B : ~astropy.units.Quantity
        The magnetic field magnitude in units convertible to tesla.

    n_e : ~astropy.units.Quantity
        The electron number density.

    Returns
    -------
    omega_uh : ~astropy.units.Quantity
        The upper hybrid frequency in radians per second.

    Raises
    ------
    TypeError
        If either of `B` or `n_e` is not a Quantity.

    ~astropy.units.UnitConversionError
        If either of `B` or `n_e` is in incorrect units.

    ValueError
        If either of `B` or `n_e` contains invalid values or are of
        incompatible dimensions.

    Warns
    -----
    ~astropy.units.UnitsWarning
        If units are not provided, SI units are assumed

    Notes
    -----
    The upper hybrid frequency is given through the relation

    .. math::
        \omega_{uh}^2 = \omega_{ce}^2 + \omega_{pe}^2

    where :math:`\omega_{ce}` is the electron gyrofrequency and
    :math:`\omega_{pe}` is the electron plasma frequency.

    Example
    -------
    >>> from astropy import units as u
    >>> upper_hybrid_frequency(0.2*u.T, n_e=5e19*u.m**-3)
    <Quantity 4.00459419e+11 rad / s>
    >>> upper_hybrid_frequency(0.2*u.T, n_e=5e19*u.m**-3, to_hz = True)
    <Quantity 6.37350961e+10 Hz>

    """
    omega_pe = plasma_frequency(n=n_e)
    omega_ce = gyrofrequency(B)
    omega_uh = (np.sqrt(omega_pe ** 2 + omega_ce ** 2))

    return omega_uh


@validate_quantities(n_i={'can_be_negative': False},
                     validations_on_return={'units': [u.rad / u.s, u.Hz],
                                            'equivalencies': [(u.cy / u.s, u.Hz)]})
@angular_freq_to_hz
def lower_hybrid_frequency(B: u.T, n_i: u.m ** -3, ion='p+') -> u.rad / u.s:
    r"""
    Return the lower hybrid frequency.

    Parameters
    ----------
    B : ~astropy.units.Quantity
        The magnetic field magnitude in units convertible to tesla.

    n_i : ~astropy.units.Quantity
        Ion number density.

    ion : str, optional
        Representation of the ion species (e.g., 'p' for protons, 'D+'
        for deuterium, or 'He-4 +1' for singly ionized helium-4),
        which defaults to protons.  If no charge state information is
        provided, then the ions are assumed to be singly charged.

    Returns
    -------
    omega_lh : ~astropy.units.Quantity
        The lower hybrid frequency in radians per second.

    Raises
    ------
    TypeError
        If either of `B` or `n_i` is not a `~astropy.units.Quantity`,
        or ion is of an inappropriate type.

    ~astropy.units.UnitConversionError
        If either of `B` or `n_i` is in incorrect units.

    ValueError
        If either of `B` or `n_i` contains invalid values or are of
        incompatible dimensions, or ion cannot be used to identify an
        ion or isotope.

    Warns
    -----
    ~astropy.units.UnitsWarning
        If units are not provided, SI units are assumed

    Notes
    -----
    The lower hybrid frequency is given through the relation

    .. math::
        \frac{1}{\omega_{lh}^2} = \frac{1}{\omega_{ci}^2 + \omega_{pi}^2} +
        \frac{1}{\omega_{ci}\omega_{ce}}

    where :math:`\omega_{ci}` is the ion gyrofrequency,
    :math:`\omega_{ce}` is the electron gyrofrequency, and
    :math:`\omega_{pi}` is the ion plasma frequency.

    Example
    -------
    >>> from astropy import units as u
    >>> lower_hybrid_frequency(0.2*u.T, n_i=5e19*u.m**-3, ion='D+')
    <Quantity 5.78372733e+08 rad / s>
    >>> lower_hybrid_frequency(0.2*u.T, n_i=5e19*u.m**-3, ion='D+', to_hz = True)
    <Quantity 92050879.32941628 Hz>

    """

    # We do not need a charge state here, so the sole intent is to
    # catch invalid ions.
    try:
        atomic.integer_charge(ion)
    except Exception:
        raise ValueError("Invalid ion in lower_hybrid_frequency.")

    omega_ci = gyrofrequency(B, particle=ion)
    omega_pi = plasma_frequency(n_i, particle=ion)
    omega_ce = gyrofrequency(B)
    omega_lh = ((omega_ci * omega_ce) ** -1 + omega_pi ** -2) ** -0.5
    # TODO possibly optimize the above line via np.sqrt
    omega_lh = omega_lh

    return omega_lh

class GPIO(object):
    def __init__(self, *args):
        print("Dummy GPIO used splash! But nothing happened...")
    
    def setup(*args):
        return None
    
    def setmode(*args):
        return None
    
    def output(*args):
        return None
    
    def OUT(*args):
        return None
    
    def LOW(*args):
        return None
    
    def BCM(*args):
        return None
    
    def HIGH(*args):
        return None
    
    def cleanup(*args):
        return None

    def IN(*args):
        return None

    def input(*args):
        return None


class pigpioPi(object):
    def __init__(self, *args):
        print("Dummy pigpio.pi used splash! But nothing happened...") 
    
    def wave_clear(*args):
        return None

    def set_servo_pulsewidth(*args):
        return None
    
    def write(*args):
        return None
    
    def set_PWM_dutycycle(*args):
        return None
    
    def set_PWM_frequency(*args):
        return None
    
    def set_mode(*args):
        return None
    
    def wave_add_generic(*args):
        return None
    
    def wave_create(*args):
        return None
    
    def wave_chain(*args):
        return None
    
    def wave_tx_busy(*args):
        return None
    
    def wave_tx_stop(*args):
        return None
    
    def wave_delete(*args):
        return None


class pigpio(object):
    def __init__(self, *args):
        print("Dummy pigpio used splash! But nothing happened...") 
    
    def pi(*args):
        return pigpioPi

    def OUTPUT(*args):
        return None

    def pulse(*args):
        return None
    

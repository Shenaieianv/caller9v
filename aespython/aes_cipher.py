try:
    from . import aes_tables
except ValueError:
    import aes_tables

class AESCipher:
    
    def __init__ (self, expanded_key):        
        #Store epanded key
        self._expanded_key = expanded_key
        
        #Number of rounds determined by expanded key length
        self._Nr = int(len(expanded_key) / 16) - 1        
        
        #Tables to replace calculation with lookups
        self._tables = aes_tables.AESTables()
        
    def _sub_bytes (self, state):
        #Run state through sbox
        return [self._tables.get_sbox(i) for i in state]
    
    def _i_sub_bytes (self, state):
        #Run state through inverted sbox
        return [self._tables.get_i_sbox(i) for i in state]
    
    def _shift_row (self, row, shift):
        #Circular shift row left by shift amount
        if (shift == 0):
            return row
        else:
            return row[shift:] + row[:shift]
    
    def _shift_rows (self, state):
        result = [0] * 16
        #Extract rows as every 4th item starting at [0..3]
        #Replace row with shift_row operation
        for i in range(4):
            result[i::4] = self._shift_row(state[i::4],i)
        return result
    
    def _i_shift_row (self, row, shift):
        #Circular shift row right by shift amount
        if (shift == 0):
            return row
        else:
            return row[-shift:] + row[:-shift] 
        
    def _i_shift_rows (self, state):
        result = [0] * 16
        #Extract rows as every 4th item starting at [0..3]
        #Replace row with inverse shift_row operation
        for i in range(4):
            result[i::4] = self._i_shift_row(state[i::4],i)
        return result
    
    def _mix_column (self, column, inverse):
        #Use galois lookup tables instead of performing complicated operations
        #If inverse, use matrix with inverse values. 
        #The matrices can be described by the galois_multipliers 
        #vectors below used in different orders
        if (inverse):
            galois_multipliers = [14, 11, 13, 9]
        else:
            galois_multipliers = [2, 3, 1, 1]
        return [
            self._tables.get_galois(galois_multipliers[0], column[0]) ^ 
            self._tables.get_galois(galois_multipliers[1], column[1]) ^
            self._tables.get_galois(galois_multipliers[2], column[2]) ^
            self._tables.get_galois(galois_multipliers[3], column[3]),
            self._tables.get_galois(galois_multipliers[3], column[0]) ^ 
            self._tables.get_galois(galois_multipliers[0], column[1]) ^
            self._tables.get_galois(galois_multipliers[1], column[2]) ^
            self._tables.get_galois(galois_multipliers[2], column[3]),
            self._tables.get_galois(galois_multipliers[2], column[0]) ^ 
            self._tables.get_galois(galois_multipliers[3], column[1]) ^
            self._tables.get_galois(galois_multipliers[0], column[2]) ^
            self._tables.get_galois(galois_multipliers[1], column[3]),
            self._tables.get_galois(galois_multipliers[1], column[0]) ^ 
            self._tables.get_galois(galois_multipliers[2], column[1]) ^
            self._tables.get_galois(galois_multipliers[3], column[2]) ^
            self._tables.get_galois(galois_multipliers[0], column[3])]
        
    def _mix_columns (self, state, inverse):
        #Perform mix_column for each column in the state
        for i in range(4):
            start = i * 4
            state[start : start + 4] = self._mix_column(state[start : start + 4], inverse)            
        return state
    
    def _add_round_key (self, state, round):
        #XOR the state with the current round key
        return [ i ^ j for i,j in zip(state, self._expanded_key[round * 16 : (round + 1) * 16])]
    
    def cipher_block (self, input):
        """Perform AES block cipher on input"""
        state = input        
        
        state = self._add_round_key(state, 0)
                
        for i in range(1, self._Nr):
            state = self._sub_bytes(state)
            state = self._shift_rows(state)
            state = self._mix_columns(state, False)
            state = self._add_round_key(state, i)
                    
        state = self._sub_bytes(state)
        state = self._shift_rows(state)
        state = self._add_round_key(state, self._Nr)
                
        return state
    
    def decipher_block (self, input):
        """Perform AES block decipher on input"""
        state = input
        
        state = self._add_round_key(state, self._Nr)
        
        for i in range(self._Nr - 1, 0, -1):
            state = self._i_shift_rows(state)
            state = self._i_sub_bytes(state)
            state = self._add_round_key(state, i)
            state = self._mix_columns(state, True)
        
        state = self._i_shift_rows(state)
        state = self._i_sub_bytes(state)
        state = self._add_round_key(state, 0)
        
        return state
    
if __name__ == "__main__":
    import test_keys
    import key_expander
    
    test_data = test_keys.TestKeys()
    
    for key_size in [128, 192, 256]:
        test_key_expander = key_expander.KeyExpander(key_size)
        test_expanded_key = test_key_expander.expand(test_data.test_key[key_size])
        test_cipher = AESCipher(test_expanded_key)
        test_result_ciphertext = test_cipher.cipher_block(test_data.test_block_plaintext)
        print ('Test',key_size,'bit cipher:', end = ' ')
        if (len([i for i, j in zip(test_result_ciphertext, test_data.test_block_ciphertext_validated[key_size]) if i == j]) == 16):
            print ('passed')
        else:
            print ('failed')
    
        test_result_plaintext = test_cipher.decipher_block(test_data.test_block_ciphertext_validated[key_size])
        print ('Test',key_size,'bit decipher:', end = ' ')
        if (len([i for i, j in zip(test_result_plaintext, test_data.test_block_plaintext) if i == j]) == 16):
            print ('passed')
        else:
            print ('failed')
    
    
    
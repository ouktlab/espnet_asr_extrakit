import sys
import threading
import queue
import socket
import struct
import numpy as np
import select

class AdinnetServer(threading.Thread):
    """ Original is a "adinserver.py" in the pyadintool (https://github.com/ouktlab/pyadintool)
    """
    def __init__(self, hostname, port, bin_dtype='int16'):
        """
        hostname: str
        port: int
        bin_dtype: str
        """
        super(AdinnetServer, self).__init__()
        self.is_finish = False
        self.sock = None
        self.client = None
        self.q = queue.Queue()  # tuple of (isEnd, audio) 

        self.hostname = hostname
        self.port = port
        self.bin_dtype = bin_dtype

    def open(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.hostname, self.port))
        self.sock.listen(1)
        print(f"[LOG]: now waiting for connection from adinnet client")

    def stop(self):
        self.is_finish = True

    def close(self, signal=None, frame=None):
        self.q.put((None, None))
        if self.client is not None:
            self.client.close()
        if self.sock is not None:
            self.sock.close()

    def check_select(self, d):
        while True:
            r,_,_ = select.select([d], [], [], 1.0)
            if len(r) > 0:
                return True
            if self.is_finish is True:
                return False

    def receive(self):
        """
        receive data from client
        """
        while self.is_finish is False:
            if self.check_select(self.client) is False:
                return
                
            # receive byte size
            m_len = self.client.recv(4)            
            if len(m_len) == 0:
                print("[LOG]: connection shutdown")
                raise Exception("connection shutdown")
                break
            
            m_len = struct.unpack('<i', m_len)[0]

            # end of segment
            if m_len == 0:
                self.q.put((True, None))
                continue
            
            # receive byte sequence
            n_left = m_len
            while n_left > 0:
                if self.check_select(self.client) is False:
                    return
                
                bindata = self.client.recv(n_left)                
                n_left -= len(bindata)
                audio = np.frombuffer(bindata, dtype=self.bin_dtype)
                self.q.put((False, audio))
            
        pass

    def run(self):
        self.open()
        while self.is_finish is False:
            try:
                if self.check_select(self.sock) is False:
                    break
                self.client, self.remote_addr = self.sock.accept()
                print(f"[LOG]: accept connection from {self.remote_addr}")
                self.receive()        
            except:
                break        
        self.close()
        
    def get(self, timeout=None):
        return self.q.get(timeout=timeout)


def loop(model, adinserver, np_dtype=np.float16, scale=32767.0):
    while True:
        try:
            isEOS, audio = adinserver.get()
            
            if isEOS is True:
                print('', file=sys.stderr, flush=True)
                results = model(
                    speech=np.empty(0, dtype=np_dtype),
                    is_final=True)
                print(f'Result -- {results[0][0]}')
                print(f'Score: {results[0][3][1].item():.2f},'
                      f' details: {results[0][3][2]}')
            else:
                audio = audio.astype(np_dtype)/scale
                results = model(speech=audio, is_final=False)
                if results is not None and len(results) > 0:
                    nbests = [text for text, token, token_int, hyp in results]
                    text = nbests[0] if nbests is not None and len(nbests) > 0 else ""
                    print(f'Real-time result -- {text}\r', file=sys.stderr, flush=True, end='')

        except Exception as e:
            print('[ERROR]: ', e)
            print('[ERROR]: abort')
            break

    adinserver.stop()
    print("[LOG]: end")


def run_espnet(hostname, port, hfrepo, beam_size, nbest, ctc_weight, lm_weight, penalty, device, token_type='char'):
    ############################
    from espnet2.bin.asr_inference_streaming import Speech2TextStreaming

    model = Speech2TextStreaming.from_pretrained(
        hfrepo,
        device=device,
        token_type=token_type,
        bpemodel=None,
        maxlenratio=0.0,
        minlenratio=0.0,
        beam_size=beam_size,
        nbest=nbest,
        ctc_weight=ctc_weight,
        lm_weight=lm_weight,
        penalty=penalty,
        disable_repetition_detection=True,
    )
    
    adinserver = AdinnetServer(hostname, port)
    adinserver.start()

    loop(model, adinserver)
    adinserver.join()

def usage():
    """
    return
        args: argparse.Namespace
    """
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('hfrepo', type=str, help='huggingface repository for ESPnet ASR')
    parser.add_argument('--hostname', type=str, default='localhost')
    parser.add_argument('--port', type=int, default=5530)
    parser.add_argument('--beam_size', type=int, default=8)
    parser.add_argument('--nbest', type=int, default=3)
    parser.add_argument('--ctc_weight', type=float, default=0.3)
    parser.add_argument('--lm_weight', type=float, default=0.1)
    parser.add_argument('--penalty', type=float, default=0.0)
    parser.add_argument('--token_type', type=str, default='char')
    parser.add_argument('--device', type=str, help='cpu, cuda', default='cuda')
    args = parser.parse_args()
    print(args)
    return args


def main():
    args = usage()
    run_espnet(**vars(args))


if __name__ == '__main__':
    main()

import torch
import torch.nn as nn
from model.core.vae import EncoderCNN, EncoderRNN

class INV_ENC(nn.Module):
    def __init__(self, task, vae_enc=None, cnn_filt=8, modulator_dim=0, content_dim=0, rnn_hidden=10, T_inv=10, device='cpu'):
        super(INV_ENC, self).__init__()
        self.modulator_dim = modulator_dim
        self.content_dim = content_dim
        if task=='rot_mnist' or task=='rot_mnist_ou':
            self.inv_encoder = InvariantEncoderCNN(task=task, out_distr='dirac', enc_out_dim=modulator_dim+content_dim, n_filt=cnn_filt, T_inv=T_inv).to(device)
        elif task=='bb':
            self.inv_encoder = InvariantEncoderCNNMLP(vae_enc, T_inv, H=64, out_dim=modulator_dim+content_dim)
        elif task=='sin' or task=='lv' or 'mocap' in task or task=='ais':
            if task=='sin':
                data_dim = 1
            elif task=='lv':
                data_dim = 2
            elif 'mocap' in task:
                data_dim = 50
            elif task=='ais':
                data_dim = 2
            self.inv_encoder = InvariantEncoderRNN(data_dim, T_inv=T_inv, rnn_hidden=rnn_hidden, enc_out_dim=modulator_dim+content_dim, out_distr='dirac').to(device)

    def kl(self):
        return torch.zeros(1) * 0.0

    def forward(self, X, L=1):
        ''' 
            X is [N,T,nc,d,d] or [N,T,q] 
            returns [L,N,T,q]
        '''
        c = self.inv_encoder(X) # N,Tinv,q or N,ns,q
        return c.repeat([L,1,1,1]) # L,N,T,q

class InvariantEncoderRCNN(nn.Module):
    def __init__(self, task, out_distr='dirac', enc_out_dim=16, n_filt=8, n_in_channels=1, T_inv=15, vae_enc=None):
        super().__init__()
        self.enc_out_dim = enc_out_dim
        if vae_enc is None:
            self.cnn_enc = EncoderCNN(task, out_distr=out_distr,  enc_out_dim=enc_out_dim, n_filt=8, n_in_channels=1)
        else:
            self.cnn_enc = nn.Sequential(vae_enc.cnn, nn.Linear(vae_enc.in_features, enc_out_dim))
        self.rnn_enc = EncoderRNN(enc_out_dim, rnn_hidden=10, enc_out_dim=enc_out_dim, out_distr=out_distr) 
        self.T_inv = T_inv
    def forward(self,X,ns=5):
        [N,T,nc,d,d] = X.shape
        z = self.cnn_enc(X.reshape(N*T,nc,d,d)).reshape(N,T,-1) # N,T,n
        T_inv = min(self.T_inv,T)
        z   = z.repeat([ns,1,1])
        t0s = torch.randint(0,T-T_inv+1,[ns*N]) 
        z   = torch.stack([z[n,t0:t0+T_inv] for n,t0 in enumerate(t0s)]) # ns*N,T_inv,d
        X_out = self.rnn_enc(z) # ns*N,enc_out_dim
        return X_out.reshape(ns,N,self.enc_out_dim).permute(1,0,2) # N,ns,enc_out_dim
    
class InvariantEncoderCNNMLP(nn.Module):
    def __init__(self, vae_enc, T_inv, H, out_dim):
        super().__init__()
        self.vae_enc = vae_enc
        self.out_dim = out_dim
        self.mlp = nn.Sequential(nn.Linear(vae_enc.H*T_inv,H), nn.ReLU(), nn.Linear(H,out_dim))
        self.T_inv = T_inv
    def forward(self,X,ns=5):
        [N,T,nc,d,d] = X.shape
        z = self.vae_enc.backbone(X.reshape(N*T,nc,d,d)).reshape(N,T,-1) # N,T,n
        T_inv = min(self.T_inv,T)
        z     = z.repeat([ns,1,1])
        t0s   = torch.randint(0,T-T_inv+1,[ns*N]) 
        z     = torch.stack([z[n,t0:t0+T_inv] for n,t0 in enumerate(t0s)]) # ns*N,T_inv,d
        X_out = self.mlp(z.reshape(ns*N, T_inv*z.shape[-1])) # ns*N,enc_out_dim
        return X_out.reshape(ns,N,self.out_dim).permute(1,0,2) # N,ns,enc_out_dim
    
class InvariantEncoderCNN(EncoderCNN):
    def __init__(self, task, out_distr='dirac', enc_out_dim=16, n_filt=8, n_in_channels=1, T_inv=15):
        super().__init__(task, out_distr=out_distr, enc_out_dim=enc_out_dim, n_filt=n_filt, n_in_channels=n_in_channels)
        self.T_inv = T_inv
    def forward(self,X):
        [N,T,nc,d,d] = X.shape
        T_inv = T//2 if self.T_inv is None else self.T_inv
        T_inv = min(T_inv,T)
        t     = torch.stack([torch.randperm(T)[:T_inv] for _ in range(N)], 1).to(X.device) # T_inv,N
        index = torch.arange(N).repeat(T_inv, 1).to(X.device) # T_inv,N
        X     = X[index.view(-1),t.view(-1)].view(T_inv * N, nc, d, d)         
        X_out = super().forward(X) # N*T,_
        return X_out.reshape(T_inv,N,self.enc_out_dim).permute(1,0,2)

class InvariantEncoderRNN(EncoderRNN):
    def __init__(self, input_dim, T_inv=None, rnn_hidden=10, enc_out_dim=16, out_distr='dirac'):
        super(InvariantEncoderRNN, self).__init__(input_dim, rnn_hidden=rnn_hidden, enc_out_dim=enc_out_dim, out_distr=out_distr)
        self.T_inv = T_inv
    def forward(self, X, ns=5):
        [N,T,d] = X.shape
        T_inv = T//2 if self.T_inv is None else self.T_inv
        T_inv = min(T_inv,T)
        X   = X.repeat([ns,1,1])
        t0s = torch.randint(0,T-T_inv+1,[ns*N]) 
        X   = torch.stack([X[n,t0:t0+T_inv] for n,t0 in enumerate(t0s)]) # ns*N,T_inv,d
        X_out = super().forward(X) # ns*N,enc_out_dim
        return X_out.reshape(ns,N,self.enc_out_dim).permute(1,0,2) # N,ns,enc_out_dim
        
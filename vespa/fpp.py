from __future__ import print_function, division

import numpy as np
import os, os.path
import logging

import matplotlib.pyplot as plt
from matplotlib import cm

from .populations import PopulationSet
from .transitsignal import TransitSignal

from plotutils import setfig
from hashutils import hashcombine



class FPPCalculation(object):
    def __init__(self, trsig, popset, lhoodcachefile=None):
        self.trsig = trsig
        self.name = trsig.name
        self.popset = popset
        self.lhoodcachefile = lhoodcachefile
        for pop in self.popset.poplist:
            pop.lhoodcachefile = lhoodcachefile
        
    def plotsignal(self,fig=None,saveplot=True,folder='.',figformat='png',**kwargs):
        self.trsig.plot(plot_tt=True,fig=fig,**kwargs)
        if saveplot:
            plt.savefig('%s/signal.%s' % (folder,figformat))
            plt.close()

    def FPPsummary(self,fig=None,figsize=(10,8),folder='.',saveplot=False,starinfo=True,siginfo=True,
                   priorinfo=True,constraintinfo=True,tag=None,simple=False,figformat='png'):
        if simple:
            starinfo = False
            siginfo = False
            priorinfo = False
            constraintinfo = False

        #print('backend being used for summary plot: %s' % matplotlib.rcParams['backend'])

        setfig(fig,figsize=figsize)
        # three pie charts
        priors = []; lhoods = []; Ls = []
        #for model in ['eb','heb','bgeb','bgpl','pl']:
        for model in self.popset.modelnames:
            priors.append(self.prior(model))
            lhoods.append(self.lhood(model))
            Ls.append(priors[-1]*lhoods[-1])
        priors = np.array(priors)
        lhoods = np.array(lhoods)
        Ls = np.array(Ls)
        logging.debug('modelnames={}'.format(self.popset.modelnames))
        logging.debug('priors={}'.format(priors))
        logging.debug('lhoods={}'.format(lhoods))

        #colors = ['b','g','r','m','c']
        nmodels = len(self.popset.modelnames)
        colors = [cm.jet(1.*i/nmodels) for i in range(nmodels)]
        legendprop = {'size':11}

        ax1 = plt.axes([0.15,0.45,0.35,0.43])
        plt.pie(priors/priors.sum(),colors=colors)
        labels = []
        #for i,model in enumerate(['eb','heb','bgeb','bgpl','pl']):
        for i,model in enumerate(self.popset.modelnames):
            labels.append('%s: %.1e' % (model,priors[i]))
        plt.legend(labels,bbox_to_anchor=(-0.25,-0.1),loc='lower left',prop=legendprop)
        plt.title('Priors')
        #p.annotate('*',xy=(0.05,0.41),xycoords='figure fraction')

        ax2 = plt.axes([0.5,0.45,0.35,0.43])
        plt.pie(lhoods/lhoods.sum(),colors=colors)
        labels = []
        #for i,model in enumerate(['eb','heb','bgeb','bgpl','pl']):
        for i,model in enumerate(self.popset.modelnames):
            labels.append('%s: %.1e' % (model,lhoods[i]))
        plt.legend(labels,bbox_to_anchor=(1.25,-0.1),loc='lower right',prop=legendprop)
        plt.title('Likelihoods')

        ax3 = plt.axes([0.3,0.03,0.4,0.5])
        plt.pie(Ls/Ls.sum(),colors=colors)
        labels = []
        #for i,model in enumerate(['eb','heb','bgeb','bgpl','pl']):
        for i,model in enumerate(self.popset.modelnames):
            labels.append('%s: %.3f' % (model,Ls[i]/Ls.sum()))
        plt.legend(labels,bbox_to_anchor=(1.6,0.44),loc='right',prop={'size':14},shadow=True)
        plt.annotate('Final Probability',xy=(0.5,-0.01),ha='center',xycoords='axes fraction',fontsize=18)

        """
        #starpars = 'Star parameters used\nin simulations'
        starpars = ''
        if 'M' in self['heb'].stars.keywords and 'DM_P' in self.keywords:
            starpars += '\n$M/M_\odot = %.2f^{+%.2f}_{-%.2f}$' % (self['M'],self['DM_P'],self['DM_N'])
        else:
            starpars += '\n$(M/M_\odot = %.2f \pm %.2f)$' % (self['M'],0)  #this might not always be right?

        if 'DR_P' in self.keywords:
            starpars += '\n$R/R_\odot = %.2f^{+%.2f}_{-%.2f}$' % (self['R'],self['DR_P'],self['DR_N'])
        else:
            starpars += '\n$R/R_\odot = %.2f \pm %.2f$' % (self['R'],self['DR'])

        if 'FEH' in self.keywords:
            if 'DFEH_P' in self.keywords:
                starpars += '\n$[Fe/H] = %.2f^{+%.2f}_{-%.2f}$' % (self['FEH'],self['DFEH_P'],self['DFEH_N'])
            else:
                starpars += '\n$[Fe/H] = %.2f \pm %.2f$' % (self['FEH'],self['DFEH'])
        for kw in self.keywords:
            if re.search('-',kw):
                try:
                    starpars += '\n$%s = %.2f (%.2f)$ ' % (kw,self[kw],self['COLORTOL'])
                except TypeError:
                    starpars += '\n$%s = %s (%.2f)$ ' % (kw,self[kw],self['COLORTOL'])
                    
        #if 'J-K' in self.keywords:
        #    starpars += '\n$J-K = %.2f (%.2f)$ ' % (self['J-K'],self['COLORTOL'])
        #if 'G-R' in self.keywords:
        #    starpars += '\n$g-r = %.2f (%.2f)$' % (self['G-R'],self['COLORTOL'])
        if starinfo:
            plt.annotate(starpars,xy=(0.03,0.91),xycoords='figure fraction',va='top')

        #p.annotate('Star',xy=(0.04,0.92),xycoords='figure fraction',va='top')

        priorpars = r'$f_{b,short} = %.2f$  $f_{trip} = %.2f$' % (self.priorfactors['fB']*self.priorfactors['f_Pshort'],
                                                                self.priorfactors['ftrip'])
        if 'ALPHA' in self.priorfactors:
            priorpars += '\n'+r'$f_{pl,bg} = %.2f$  $\alpha_{pl,bg} = %.1f$' % (self.priorfactors['fp'],self['ALPHA'])
        else:
            priorpars += '\n'+r'$f_{pl,bg} = %.2f$  $\alpha_1,\alpha_2,r_b = %.1f,%.1f,%.1f$' % \
                         (self.priorfactors['fp'],self['bgpl'].stars.keywords['ALPHA1'],
                          self['bgpl'].stars.keywords['ALPHA2'],
                          self['bgpl'].stars.keywords['RBREAK'])
            
        rbin1,rbin2 = self['RBINCEN']-self['RBINWID'],self['RBINCEN']+self['RBINWID']
        priorpars += '\n$f_{pl,specific} = %.2f, \in [%.2f,%.2f] R_\oplus$' % (self.priorfactors['fp_specific'],rbin1,rbin2)
        priorpars += '\n$r_{confusion} = %.1f$"' % sqrt(self.priorfactors['area']/pi)
        if self.priorfactors['multboost'] != 1:
            priorpars += '\nmultiplicity boost = %ix' % self.priorfactors['multboost']
        if priorinfo:
            plt.annotate(priorpars,xy=(0.03,0.4),xycoords='figure fraction',va='top')
        

        sigpars = ''
        sigpars += '\n$P = %s$ d' % self['P']
        depth,ddepth = self.trsig.depthfit
        sigpars += '\n$\delta = %i^{+%i}_{-%i}$ ppm' % (depth*1e6,ddepth[1]*1e6,ddepth[0]*1e6)
        dur,ddur = self.trsig.durfit
        sigpars += '\n$T = %.2f^{+%.2f}_{-%.2f}$ h' % (dur*24.,ddur[1]*24,ddur[0]*24)
        slope,dslope = self.trsig.slopefit
        sigpars += '\n'+r'$T/\tau = %.1f^{+%.1f}_{-%.1f}$' % (slope,dslope[1],dslope[0])
        sigpars += '\n'+r'$(T/\tau)_{max} = %.1f$' % (self.trsig.maxslope)
        if siginfo:
            plt.annotate(sigpars,xy=(0.81,0.91),xycoords='figure fraction',va='top')
        
            #p.annotate('${}^a$Not used for FP population simulations',xy=(0.02,0.02),
            #           xycoords='figure fraction',fontsize=9)
        """

        constraints = 'Constraints:'
        for c in self.popset.constraints:
            try:
                constraints += '\n  %s' % self['heb'].constraints[c]
            except KeyError:
                constraints += '\n  %s' % self['beb'].constraints[c]                
        if constraintinfo:
            plt.annotate(constraints,xy=(0.03,0.22),xycoords='figure fraction',
                         va='top',color='red')
            
        odds = 1./self.FPP()
        if odds > 1e6:
            fppstr = 'FPP: < 1 in 1e6' 
        else:
            fppstr = 'FPP: 1 in %i' % odds
            
        plt.annotate('$f_{pl,V} = %.3f$\n%s' % (self.fpV(),fppstr),xy=(0.7,0.02),
                     xycoords='figure fraction',fontsize=16,va='bottom')

        plt.suptitle(self.trsig.name,fontsize=22)

        #if not simple:
        #    plt.annotate('n = %.0e' % self.n,xy=(0.5,0.85),xycoords='figure fraction',
        #                 fontsize=14,ha='center')

        if saveplot:
            if tag is not None:
                plt.savefig('%s/FPPsummary_%s.%s' % (folder,tag,figformat))
            else:
                plt.savefig('%s/FPPsummary.%s' % (folder,figformat))
            plt.close()


    def lhoodplots(self,folder='.',tag=None,figformat='png',**kwargs):
        Ltot = 0
        #print('backend being used for lhoodplots: %s' % matplotlib.rcParams['backend'])
        #for model in ['eb','heb','bgeb','bgpl','pl']:
        for model in self.popset.modelnames:
            Ltot += self.prior(model)*self.lhood(model)
        
        #for model in ['eb','heb','bgeb','bgpl','pl']:
        for model in self.popset.shortmodelnames:
            self.lhoodplot(model,Ltot=Ltot,**kwargs)
            if tag is None:
                plt.savefig('%s/%s.%s' % (folder,model,figformat))
            else:
                plt.savefig('%s/%s_%s.%s' % (folder,model,figformat))
            plt.close()

    def lhoodplot(self,model,suptitle='',**kwargs):
        if suptitle=='':
            suptitle = self[model].model
        self[model].lhoodplot(self.trsig,colordict=self.popset.colordict,
                              suptitle=suptitle,**kwargs)

    def calc_lhoods(self,verbose=True,**kwargs):
        if verbose:
            logging.info('Calculating likelihoods...')
        for pop in self.popset.poplist:
            L = pop.lhood(self.trsig,**kwargs)
            if verbose:
                logging.info('%s: %.2e' % (pop.model,L))

    def __hash__(self):
        return hashcombine(self.popset, self.trsig)

    def __getitem__(self,model):
        return self.popset[model]

    def prior(self,model):
        return self[model].prior

    def lhood(self,model,**kwargs):
        return self[model].lhood(self.trsig,
                                 **kwargs)

    def Pval(self,skipmodels=None,verbose=False):
        Lfpp = 0
        if skipmodels is None:
            skipmodels = []
        if verbose:
            logging.info('evaluating likelihoods for %s' % self.trsig.name)
        
        for model in self.popset.modelnames:
            if model=='Planets':
                continue
            if model not in skipmodels:
                prior = self.prior(model)
                lhood = self.lhood(model)
                Lfpp += prior*lhood
                if verbose:
                    logging.info('%s: %.2e = %.2e (prior) x %.2e (lhood)' % (model,prior*lhood,prior,lhood))
        prior = self.prior('pl')
        lhood = self.lhood('pl')
        Lpl = prior*lhood
        if verbose:
            logging.info('planet: %.2e = %.2e (prior) x %.2e (lhood)' % (prior*lhood,prior,lhood))
        return Lpl/Lfpp/self['pl'].priorfactors['fp_specific']

    def fpV(self,FPPV=0.005,skipmodels=None,verbose=False):
        P = self.Pval(skipmodels=skipmodels,verbose=verbose)
        return (1-FPPV)/(P*FPPV)

    def FPP(self,skipmodels=None,verbose=False):
        Lfpp = 0
        if skipmodels is None:
            skipmodels = []
        if verbose:
            logging.info('evaluating likelihoods for %s' % self.trsig.name)
        for model in self.popset.modelnames:
            if model=='Planets':
                continue
            if model not in skipmodels:
                prior = self.prior(model)
                lhood = self.lhood(model)
                Lfpp += prior*lhood
                if verbose:
                    logging.info('%s: %.2e = %.2e (prior) x %.2e (lhood)' % (model,prior*lhood,prior,lhood))
        prior = self.prior('pl')
        lhood = self.lhood('pl')
        Lpl = prior*lhood
        if verbose:
            logging.info('planet: %.2e = %.2e (prior) x %.2e (lhood)' % (prior*lhood,prior,lhood))
        return 1 - Lpl/(Lpl + Lfpp)

    def set_maxrad(self,*args,**kwargs):
        self.popset.set_maxrad(*args,**kwargs)

    def change_prior(self,**kwargs):
        self.popset.change_prior(**kwargs)

    def ruleout_model(self,*args,**kwargs):
        self.popset.ruleout_model(*args,**kwargs)

    def apply_multicolor_transit(self,*args,**kwargs):
        self.popset.apply_multicolor_transit(*args,**kwargs)

    def apply_dmaglim(self,*args,**kwargs):
        self.popset.apply_dmaglim(*args,**kwargs)
        self.dmaglim = self.popset.dmaglim

    def apply_secthresh(self,*args,**kwargs):
        self.popset.apply_secthresh(*args,**kwargs)
        self.secthresh = self.popset.secthresh

    def apply_trend_constraint(self,*args,**kwargs):
        self.popset.apply_trend_constraint(*args,**kwargs)
        self.trend_limit = self.popset.trend_limit
        self.trend_dt = self.popset.trend_dt

    def constrain_Teff(self,T,dT=80,**kwargs):
        self.constrain_property('Teff',measurement=(T,dT),selectfrac_skip=True,**kwargs)

    def constrain_logg(self,g,dg=0.15,**kwargs):
        self.constrain_property('logg',measurement=(g,dg),selectfrac_skip=True,**kwargs)

    def constrain_property(self,*args,**kwargs):
        self.popset.constrain_property(*args,**kwargs)

    def replace_constraint(self,*args,**kwargs):
        self.popset.replace_constraint(*args,**kwargs)

    def remove_constraint(self,*args,**kwargs):
        self.popset.remove_constraint(*args,**kwargs)

    def apply_cc(self,cc):
        logging.info('applying %s band contrast curve to %s.' % (cc.band,self.name))
        self.popset.apply_cc(cc)

    def apply_vcc(self,*args,**kwargs):
        self.popset.apply_vcc(*args,**kwargs)


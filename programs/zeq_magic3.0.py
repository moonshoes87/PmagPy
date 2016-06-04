#!/usr/bin/env python

# -*- python-indent-offset: 4; -*-

import pandas as pd
import sys
import os
import matplotlib
if matplotlib.get_backend() != "TKAgg":
    matplotlib.use("TKAgg")

import pmagpy.pmag as pmag
import pmagpy.pmagplotlib as pmagplotlib
import new_builder as nb



def save_redo(SpecRecs,inspec):
    print "Saving changes to specimen file"
    pmag.magic_write(inspec,SpecRecs,'pmag_specimens')

def main():
    """
    NAME
        zeq_magic.py

    DESCRIPTION
        reads in magic_measurements formatted file, makes plots of remanence decay
        during demagnetization experiments.  Reads in prior interpretations saved in 
        a pmag_specimens formatted file and  allows re-interpretations of best-fit lines
        and planes and saves (revised or new) interpretations in a pmag_specimens file.  
        interpretations are saved in the coordinate system used. Also allows judicious editting of
        measurements to eliminate "bad" measurements.  These are marked as such in the magic_measurements
        input file.  they are NOT deleted, just ignored. 

    SYNTAX
        zeq_magic.py [command line options]

    OPTIONS
        -h prints help message and quits
        -f  MEASFILE: sets magic_measurements format input file, default: magic_measurements.txt
        -fsp SPECFILE: sets pmag_specimens format file with prior interpreations, default: zeq_specimens.txt
        -Fp PLTFILE: sets filename for saved plot, default is name_type.fmt (where type is zijd, eqarea or decay curve)
        -crd [s,g,t]: sets coordinate system,  g=geographic, t=tilt adjusted, default: specimen coordinate system
        -fsa SAMPFILE: sets er_samples format file with orientation information, default: er_samples.txt
        -spc SPEC  plots single specimen SPEC, saves plot with specified format 
              with optional -dir settings and quits
        -dir [L,P,F][beg][end]: sets calculation type for principal component analysis, default is none
             beg: starting step for PCA calculation
             end: ending step for PCA calculation
             [L,P,F]: calculation type for line, plane or fisher mean
             must be used with -spc option
        -fmt FMT: set format of saved plot [png,svg,jpg]
        -A:  suppresses averaging of  replicate measurements, default is to average
        -sav: saves all plots without review
    SCREEN OUTPUT:
        Specimen, N, a95, StepMin, StepMax, Dec, Inc, calculation type

    """
    # initialize some variables
    doave,e,b=1,0,0 # average replicates, initial end and beginning step
    plots,coord=0,'s'
    noorient=0
    version_num=pmag.get_version()
    verbose=pmagplotlib.verbose
    calculation_type,fmt="","svg"
    user,spec_keys,locname="",[],''
    sfile=""
    geo,tilt,ask=0,0,0
    PriorRecs=[] # empty list for prior interpretations
    backup=0
    specimen="" # can skip everything and just plot one specimen with bounds e,b
    if '-h' in sys.argv:
        print main.__doc__
        sys.exit()
    dir_path = pmag.get_named_arg_from_sys("-WD", default_val=os.getcwd())
    meas_file = pmag.get_named_arg_from_sys("-f", default_val="measurements.txt") 
    #full_meas_file=os.path.join(dir_path,meas_file)
    spec_file=pmag.get_named_arg_from_sys("-fsp", default_val="specimens.txt")
    samp_file=pmag.get_named_arg_from_sys("-fsa",default_val="")
    if samp_file!="":sfile='ok'
    samp_file=os.path.join(dir_path,samp_file)
    plot_file=pmag.get_named_arg_from_sys("-Fp",default_val="")
    crd = pmag.get_named_arg_from_sys("-crd", default_val="g")
    if crd == "s":
        coord = "-1"
    elif crd == "t":
        coord = "100"
    else:
        coord = "0"
    fmt = pmag.get_named_arg_from_sys("-fmt", "svg")
    specimen=pmag.get_named_arg_from_sys("-spc",default_val="")
    beg_pca,end_pca,direction_type="","",'L'
    if '-dir' in sys.argv:
        ind=sys.argv.index('-dir')
        direction_type=sys.argv[ind+1]
        beg_pca=int(sys.argv[ind+2])
        end_pca=int(sys.argv[ind+3])
        if direction_type=='L':calculation_type='DE-BFL'
        if direction_type=='P':calculation_type='DE-BFP'
        if direction_type=='F':calculation_type='DE-FM'
    if '-A' in sys.argv: doave=0
    if '-sav' in sys.argv: plots,verbose=1,0
    #
    first_save=1
    fnames = {'measurements': meas_file, 'specimens': spec_file}
    contribution = nb.Contribution(dir_path, custom_filenames=fnames, read_tables=['measurements', 'specimens'])
    meas_container = contribution.tables['measurements']
    meas_data = meas_container.df
    if 'specimens' in contribution.tables:
        spec_container = contribution.tables['specimens']
        spec_data=spec_container.df
        spec_data= spec_data[spec_data['method_codes'].str.contains('DE-')==True] # select only directional records
        if 'software_packages' not in spec_data.columns:spec_data.software_packages=version_num
        spec_data.loc[spec_data['software_packages'].notnull(),'software_packages']=version_num
        if 'dir_comp_name' not in spec_data.columns:spec_data.dir_comp_name='A'
        spec_data.loc[spec_data['dir_comp_name'].isnull(),'dir_comp_name']='A'
    else:
       	spec_container, spec_data = None, None
    changeM,changeS=0,0 # check if data or interpretations have changed
    #for Rec in PriorRecs:
            #if 'DE-FM' in methods:
            #    Rec['calculation_type']='DE-FM' # this won't be imported but helps
            #if 'DE-BFL' in methods:
            #    Rec['calculation_type']='DE-BFL'
            #if 'DE-BFL-A' in methods:
            #    Rec['calculation_type']='DE-BFL-A'
            #if 'DE-BFL-O' in methods:
            #    Rec['calculation_type']='DE-BFL-O'
            #if 'DE-BFP' in methods:
            #    Rec['calculation_type']='DE-BFP'
        #else:
        #    Rec['calculation_type']='DE-BFL' # default is to assume a best-fit line
    #
    # get list of unique specimen names
    #
    sids= spec_data.specimen_name.unique()
    #
    #  set up plots, angle sets X axis to horizontal,  direction_type 'l' is best-fit line
    # direction_type='p' is great circle
    #     
    #
    # draw plots for sample s - default is just to step through zijderveld diagrams
    #
    #
    # define figure numbers for equal area, zijderveld,  
    #  and intensity vs. demagnetiztion step respectively
    ZED={}
    ZED['eqarea'],ZED['zijd'],  ZED['demag']=1,2,3 
    pmagplotlib.plot_init(ZED['eqarea'],6,6)
    pmagplotlib.plot_init(ZED['zijd'],6,6)
    pmagplotlib.plot_init(ZED['demag'],6,6)
    save_pca=0
    if specimen=="":
        k = 0
    else:
        k=sids.index(specimen)
    angle,direction_type="",""
    setangle=0
    CurrRecs=[]
    while k < len(sids):
        CurrRecs=[]
        if setangle==0:angle=""
        method_codes,inst_code=[],""
        s=sids[k]
        PmagSpecRec={}
        PmagSpecRec["analyst_mail_names"]=user
        PmagSpecRec['software_packages']=version_num
        PmagSpecRec['specimen_description']=""
        PmagSpecRec['method_codes']=""
        if verbose and  s!="":print s, k , 'out of ',len(sids)
    #
    #  collect info for the PmagSpecRec dictionary
    #
        s_meas= meas_data[meas_data['specimen_name'].str.contains(s)==True] # fish out this specimen
        s_meas= s_meas[s_meas['method_codes'].str.contains('LT-NO|LT-AF-Z|LT-T-Z')==True] # fish out zero field steps specimen
        print s_meas.columns
        raw_input()
        if len(s_meas)>0:
          for rec in  s_meas: # fix up a few things for the output record 
               print rec
               ##if 'instrument_codes' in rec.keys():PmagSpecRec["instrument_codes"]=rec["instrument_codes"]  # copy over instruments
               #PmagSpecRec["er_citation_names"]="This study"
               #PmagSpecRec["er_specimen_name"]=s
               #PmagSpecRec["er_sample_name"]=rec["er_sample_name"]
               #PmagSpecRec["er_site_name"]=rec["er_site_name"]
               #PmagSpecRec["er_location_name"]=rec["er_location_name"]
               #locname=rec['er_location_name']
               #if 'er_expedition_name' in rec.keys(): PmagSpecRec["er_expedition_name"]=rec["er_expedition_name"]
               #PmagSpecRec["magic_method_codes"]=rec["magic_method_codes"]
               #if "magic_experiment_name" not in rec.keys():
               #    PmagSpecRec["magic_experiment_names"]=""
               #else:    
               #    PmagSpecRec["magic_experiment_names"]=rec["magic_experiment_name"]
               #break
    #
    # find the data from the meas_data file for this specimen
    #
          data,units=pmag.find_dmag_rec(s,meas_data)
          PmagSpecRec["measurement_step_unit"]= units
          u=units.split(":")
          if "T" in units:PmagSpecRec["magic_method_codes"]=PmagSpecRec["magic_method_codes"]+":LP-DIR-AF"
          if "K" in units:PmagSpecRec["magic_method_codes"]=PmagSpecRec["magic_method_codes"]+":LP-DIR-T"
          if "J" in units:PmagSpecRec["magic_method_codes"]=PmagSpecRec["magic_method_codes"]+":LP-DIR-M"
    #
    # find prior interpretation
    #
          if len(CurrRecs)==0: # check if already in
            beg_pca,end_pca="",""
            calculation_type=""
            if inspec !="":
              if verbose: print "    looking up previous interpretations..."
              precs=pmag.get_dictitem(PriorRecs,'er_specimen_name',s,'T') # get all the prior recs with this specimen name
              precs=pmag.get_dictitem(precs,'magic_method_codes','LP-DIR','has') # get the directional data
              PriorRecs=pmag.get_dictitem(PriorRecs,'er_specimen_name',s,'F') # take them all out of prior recs
         # get the ones that meet the current coordinate system
              for prec in precs:
                if 'specimen_tilt_correction' not in prec.keys() or prec['specimen_tilt_correction']=='-1':
                    crd='s'
                elif prec['specimen_tilt_correction']=='0':
                    crd='g'
                elif prec['specimen_tilt_correction']=='100':
                    crd='t'
                else:
                    crd='?'
                CurrRec={}
                for key in prec.keys():CurrRec[key]=prec[key]
                CurrRecs.append(CurrRec) # put in CurrRecs
                method_codes= CurrRec["magic_method_codes"].replace(" ","").split(':')
                calculation_type='DE-BFL'
                if 'DE-FM' in method_codes: calculation_type='DE-FM'
                if 'DE-BFP' in method_codes: calculation_type='DE-BFP'
                if 'DE-BFL-A' in method_codes: calculation_type='DE-BFL-A'
                if 'specimen_dang' not in CurrRec.keys():
                    if verbose:print 'Run mk_redo.py and zeq_magic_redo.py to get the specimen_dang values'
                    CurrRec['specimen_dang']=-1
                if calculation_type!='DE-FM' and crd==coord: # not a fisher mean
                    if verbose:print "Specimen  N    MAD    DANG  start     end      dec     inc  type  component coordinates"
                    if units=='K':
                            if verbose:print '%s %i %7.1f %7.1f %7.1f %7.1f %7.1f %7.1f  %s  %s       %s \n' % (CurrRec["er_specimen_name"],int(CurrRec["specimen_n"]),float(CurrRec["specimen_mad"]),float(CurrRec["specimen_dang"]),float(CurrRec["measurement_step_min"])-273,float(CurrRec["measurement_step_max"])-273,float(CurrRec["specimen_dec"]),float(CurrRec["specimen_inc"]),calculation_type,CurrRec['specimen_comp_name'],crd)
                    elif units=='T':
                       if verbose:print '%s %i %7.1f %7.1f %7.1f %7.1f %7.1f %7.1f  %s  %s %s \n' % (CurrRec["er_specimen_name"],int(CurrRec["specimen_n"]),float(CurrRec["specimen_mad"]),float(CurrRec["specimen_dang"]),float(CurrRec["measurement_step_min"])*1e3,float(CurrRec["measurement_step_max"])*1e3,float(CurrRec["specimen_dec"]),float(CurrRec["specimen_inc"]),calculation_type,CurrRec['specimen_comp_name'],crd)
                    elif 'T' in units and 'K' in units:
                            if float(CurrRec['measurement_step_min'])<1.0 :
                                min=float(CurrRec['measurement_step_min'])*1e3
                            else:
                                min=float(CurrRec['measurement_step_min'])-273
                            if float(CurrRec['measurement_step_max'])<1.0 :
                                max=float(CurrRec['measurement_step_max'])*1e3
                            else:
                                max=float(CurrRec['measurement_step_max'])-273
                            if verbose:print '%s %i %7.1f %i %i %7.1f %7.1f %7.1f, %s        %s\n' % (CurrRec["er_specimen_name"],int(CurrRec["specimen_n"]),float(CurrRec["specimen_mad"]),float(CurrRec['specimen_dang']),min,max,float(CurrRec["specimen_dec"]),float(CurrRec["specimen_inc"]),calculation_type,crd)
                    elif 'J' in units:
                       if verbose:print '%s %i %7.1f %7.1f %7.1f %7.1f %7.1f %7.1f  %s  %s       %s \n' % (CurrRec["er_specimen_name"],int(CurrRec["specimen_n"]),float(CurrRec["specimen_mad"]),float(CurrRec['specimen_dang']),float(CurrRec["measurement_step_min"]),float(CurrRec["measurement_step_max"]),float(CurrRec["specimen_dec"]),float(CurrRec["specimen_inc"]),calculation_type,CurrRec['specimen_comp_name'],crd)
                elif calculation_type=='DE-FM' and crd==coord: # fisher mean
                    if verbose:print "Specimen  a95 DANG   start     end      dec     inc  type  component coordinates"
                    if units=='K':
                         if verbose:print '%s %i %7.1f %7.1f %7.1f %7.1f %7.1f  %s  %s       %s \n' % (CurrRec["er_specimen_name"],int(CurrRec["specimen_n"]),float(CurrRec["specimen_alpha95"]),float(CurrRec["measurement_step_min"])-273,float(CurrRec["measurement_step_max"])-273,float(CurrRec["specimen_dec"]),float(CurrRec["specimen_inc"]),calculation_type,CurrRec['specimen_comp_name'],crd)
                    elif units=='T':
                          if verbose:print '%s %i %7.1f %7.1f %7.1f %7.1f %7.1f  %s  %s       %s \n' % (CurrRec["er_specimen_name"],int(CurrRec["specimen_n"]),float(CurrRec["specimen_alpha95"]),float(CurrRec["measurement_step_min"])*1e3,float(CurrRec["measurement_step_max"])*1e3,float(CurrRec["specimen_dec"]),float(CurrRec["specimen_inc"]),calculation_type,CurrRec['specimen_comp_name'],crd)
                    elif 'T' in units and 'K' in units:
                            if float(CurrRec['measurement_step_min'])<1.0 :
                                min=float(CurrRec['measurement_step_min'])*1e3
                            else:
                                min=float(CurrRec['measurement_step_min'])-273
                            if float(CurrRec['measurement_step_max'])<1.0 :
                                max=float(CurrRec['measurement_step_max'])*1e3
                            else:
                                max=float(CurrRec['measurement_step_max'])-273
                            if verbose:print '%s %i %7.1f %i %i %7.1f %7.1f %s       %s \n' % (CurrRec["er_specimen_name"],int(CurrRec["specimen_n"]),float(CurrRec["specimen_alpha95"]),min,max,float(CurrRec["specimen_dec"]),float(CurrRec["specimen_inc"]),calculation_type,crd)
                    elif 'J' in units:
                       if verbose:print '%s %i %7.1f %7.1f %7.1f %7.1f %7.1f %s %s       %s \n' % (CurrRec["er_specimen_name"],int(CurrRec["specimen_n"]),float(CurrRec["specimen_mad"]),float(CurrRec["measurement_step_min"]),float(CurrRec["measurement_step_max"]),float(CurrRec["specimen_dec"]),float(CurrRec["specimen_inc"]),calculation_type,CurrRec['specimen_comp_name'],crd)
              if len(CurrRecs)==0:beg_pca,end_pca="",""
          datablock=data
          noskip=1
          if len(datablock) <3: 
            noskip=0
            if backup==0:
                k+=1
            else:
                k-=1
            if len(CurrRecs)>0:
                for rec in CurrRecs:
                    PriorRecs.append(rec)
            CurrRecs=[]
          else:
            backup=0 
          if noskip:
        #
        # find replicate measurements at given treatment step and average them
        #
#            step_meth,avedata=pmag.vspec(data)
#            if len(avedata) != len(datablock):
#                if doave==1: 
#                    method_codes.append("DE-VM")
#                    datablock=avedata
#        #
        # do geo or stratigraphic correction now
        #
            if geo==1:
        #
        # find top priority orientation method
                orient,az_type=pmag.get_orient(samp_data,PmagSpecRec["er_sample_name"])
                if az_type=='SO-NO':
                    if verbose: print "no orientation data for ",s 
                    orient["sample_azimuth"]=0
                    orient["sample_dip"]=0
                    noorient=1
                    method_codes.append("SO-NO")
                    orient["sample_azimuth"]=0
                    orient["sample_dip"]=0
                    orient["sample_bed_dip_azimuth"]=0
                    orient["sample_bed_dip"]=0
                    noorient=1
                    method_codes.append("SO-NO")
                else: 
                    noorient=0
        #
        #  if stratigraphic selected,  get stratigraphic correction
        #
                tiltblock,geoblock=[],[]
                for rec in datablock:
                    d_geo,i_geo=pmag.dogeo(rec[1],rec[2],float(orient["sample_azimuth"]),float(orient["sample_dip"]))
                    geoblock.append([rec[0],d_geo,i_geo,rec[3],rec[4],rec[5],rec[6]])
                    if tilt==1 and "sample_bed_dip" in orient.keys() and float(orient['sample_bed_dip'])!=0: 
                        d_tilt,i_tilt=pmag.dotilt(d_geo,i_geo,float(orient["sample_bed_dip_direction"]),float(orient["sample_bed_dip"]))
                        tiltblock.append([rec[0],d_tilt,i_tilt,rec[3],rec[4],rec[5],rec[6]])
                    if tilt==1: plotblock=tiltblock
                    if geo==1 and tilt==0:plotblock=geoblock
            if geo==0 and tilt==0: plotblock=datablock
    #
    # set the end pca point to last point  if not set
            if e==0 or e>len(plotblock)-1: e=len(plotblock)-1
            if angle=="": angle=plotblock[0][1] # rotate to NRM declination
            title=s+'_s'
            if geo==1 and tilt==0 and noorient!=1:title=s+'_g'
            if tilt==1 and noorient!=1:title=s+'_t'
            pmagplotlib.plotZED(ZED,plotblock,angle,title,units)
            if verbose:pmagplotlib.drawFIGS(ZED)
            if len(CurrRecs)!=0:
                for prec in CurrRecs:
                    if 'calculation_type' not in prec.keys():
                        calculation_type=''
                    else:
                        calculation_type=prec["calculation_type"]
                    direction_type=prec["specimen_direction_type"]
                    if calculation_type !="":
                        beg_pca,end_pca="",""
                        for j in range(len(datablock)):
                            if data[j][0]==float(prec["measurement_step_min"]):beg_pca=j
                            if data[j][0]==float(prec["measurement_step_max"]):end_pca=j
                        if beg_pca=="" or end_pca=="":  
                            if verbose:
                                print "something wrong with prior interpretation "
                            break
                    if calculation_type!="":
                        if beg_pca=="":beg_pca=0
                        if end_pca=="":end_pca=len(plotblock)-1
                        if geo==1 and tilt==0:
                            mpars=pmag.domean(geoblock,beg_pca,end_pca,calculation_type)
                            if mpars["specimen_direction_type"]!="Error":
                                pmagplotlib.plotDir(ZED,mpars,geoblock,angle)
                                if verbose:pmagplotlib.drawFIGS(ZED)
                        if geo==1 and tilt==1:
                            mpars=pmag.domean(tiltblock,beg_pca,end_pca,calculation_type)
                            if mpars["specimen_direction_type"]!="Error":
                                pmagplotlib.plotDir(ZED,mpars,tiltblock,angle)
                                if verbose:pmagplotlib.drawFIGS(ZED)
                        if geo==0 and tilt==0: 
                            mpars=pmag.domean(datablock,beg_pca,end_pca,calculation_type)
                        if mpars["specimen_direction_type"]!="Error":
                                pmagplotlib.plotDir(ZED,mpars,plotblock,angle)
                                if verbose:pmagplotlib.drawFIGS(ZED)
    #
    # print out data for this sample to screen
    #
            recnum=0
            for plotrec in plotblock:
                if units=='T' and verbose: print '%s: %i  %7.1f %s  %8.3e %7.1f %7.1f %s' % (plotrec[5], recnum,plotrec[0]*1e3," mT",plotrec[3],plotrec[1],plotrec[2],plotrec[6])
                if units=="K" and verbose: print '%s: %i  %7.1f %s  %8.3e %7.1f %7.1f %s' % (plotrec[5], recnum,plotrec[0]-273,' C',plotrec[3],plotrec[1],plotrec[2],plotrec[6])
                if units=="J" and verbose: print '%s: %i  %7.1f %s  %8.3e %7.1f %7.1f %s' % (plotrec[5], recnum,plotrec[0],' J',plotrec[3],plotrec[1],plotrec[2],plotrec[6])
                if 'K' in units and 'T' in units:
                    if plotrec[0]>=1. and verbose: print '%s: %i  %7.1f %s  %8.3e %7.1f %7.1f %s' % (plotrec[5], recnum,plotrec[0]-273,' C',plotrec[3],plotrec[1],plotrec[2],plotrec[6])
                    if plotrec[0]<1. and  verbose: print '%s: %i  %7.1f %s  %8.3e %7.1f %7.1f %s' % (plotrec[5], recnum,plotrec[0]*1e3," mT",plotrec[3],plotrec[1],plotrec[2],plotrec[6])
                recnum += 1
            if specimen!="":
                if plot_file=="":
                    basename=locname+'_'+s
                else:
                    basename=plot_file
                files={}
                for key in ZED.keys():
                    files[key]=basename+'_'+key+'.'+fmt 
                pmagplotlib.saveP(ZED,files)
                sys.exit()
            else:  # interactive
              if plots==0:
                ans='b'
                k+=1
                changeS=0
                while ans != "":
                    if len(CurrRecs)==0:
                        print """
                g/b: indicates  good/bad measurement.  "bad" measurements excluded from calculation

                set s[a]ve plot, [b]ounds for pca and calculate, [p]revious, [s]pecimen, 
                 change [h]orizontal projection angle,   change [c]oordinate systems, 
                 [e]dit data,  [q]uit: 
                """
                    else:
                        print """
                g/b: indicates  good/bad measurement.  "bad" measurements excluded from calculation

                 set s[a]ve plot, [b]ounds for pca and calculate, [p]revious, [s]pecimen, 
                 change [h]orizontal projection angle,   change [c]oordinate systems, 
                 [d]elete current interpretation(s), [e]dit data,   [q]uit: 
                """
                    ans=raw_input('<Return>  for  next specimen \n')
                    setangle=0
                    if ans=='d': # delete this interpretation
                        CurrRecs=[]
                        k-=1 # replot same specimen
                        ans=""
                        changeS=1
                    if  ans=='q': 
                        if changeM==1:
                            ans=raw_input('Save changes to magic_measurements.txt? y/[n] ')
                            if ans=='y':
                                pmag.magic_write(meas_file,meas_data,'magic_measurements')
                        print "Good bye"
                        sys.exit()
                    if  ans=='a':
                        if plot_file=="":
                            basename=locname+'_'+s+'_'
                        else:
                            basename=plot_file
                        files={}
                        for key in ZED.keys():
                            files[key]=basename+'_'+coord+'_'+key+'.'+fmt 
                        pmagplotlib.saveP(ZED,files)
                        ans=""
                    if  ans=='p':
                        k-=2
                        ans=""
                        backup=1
                    if ans=='c':
                        k-=1 # replot same block
                        if tilt==0 and geo ==1:print "You  are currently viewing geographic  coordinates "
                        if tilt==1 and geo ==1:print "You  are currently viewing stratigraphic  coordinates "
                        if tilt==0 and geo ==0: print "You  are currently viewing sample coordinates "
                        print "\n Which coordinate system do you wish to view? "
                        coord=raw_input(" <Return>  specimen, [g] geographic, [t] tilt corrected ")
                        if coord=="g":geo,tilt=1,0
                        if coord=="t":
                            geo=1
                            tilt=1
                        if coord=="":
                            coord='s'
                            geo=0
                            tilt=0
                        if geo==1 and sfile=="":
                            samp_file=raw_input(" Input er_samples file for sample orientations [er_samples.txt] " )
                            if samp_file=="":samp_file="er_samples.txt"
                            samp_data,file_type=pmag.magic_read(samp_file)
                            if file_type != 'er_samples':
                               print file_type
                               print "This is not a valid er_samples file - coordinate system not changed" 
                            else:
                               sfile="ok"
                        ans=""
                    if ans=='s':
                        keepon=1
                        sample=raw_input('Enter desired specimen name (or first part there of): ')
                        while keepon==1:
                            try:
                                k =sids.index(sample)
                                keepon=0
                            except:
                                tmplist=[]
                                for qq in range(len(sids)):
                                    if sample in sids[qq]:tmplist.append(sids[qq])
                                print sample," not found, but this was: "
                                print tmplist
                                sample=raw_input('Select one or try again\n ')
                        angle,direction_type="",""
                        setangle=0
                        ans=""
                    if ans=='h':
                        k-=1
                        angle=raw_input("Enter desired  declination for X axis 0-360 ")
                        angle=float(angle)
                        if angle==0:angle=0.001
                        s=sids[k]
                        setangle=1
                        ans=""
                    if  ans=='e':
                        k-=1
                        ans=""
                        recnum=0
                        for plotrec in plotblock:
                            if plotrec[0]<=200 and verbose: print '%s: %i  %7.1f %s  %8.3e %7.1f %7.1f ' % (plotrec[5], recnum,plotrec[0]*1e3," mT",plotrec[3],plotrec[1],plotrec[2])
                            if plotrec[0]>200 and verbose: print '%s: %i  %7.1f %s  %8.3e %7.1f %7.1f ' % (plotrec[5], recnum,plotrec[0]-273,' C',plotrec[3],plotrec[1],plotrec[2])
                            recnum += 1
                        answer=raw_input('Enter index of point to change from bad to good or vice versa:  ')
                        try: 
                                ind=int(answer)
                                meas_data=pmag.mark_dmag_rec(s,ind,meas_data)
                                changeM=1
                        except:
                                'bad entry, try again'
                    if  ans=='b':
                        if end_pca=="":end_pca=len(plotblock)-1
                        if beg_pca=="":beg_pca=0
                        k-=1   # stay on same sample until through
                        GoOn=0
                        while GoOn==0:
                            print 'Enter index of first point for pca: ','[',beg_pca,']'
                            answer=raw_input('return to keep default  ')
                            if answer != "":
                                beg_pca=int(answer)
                            print 'Enter index  of last point for pca: ','[',end_pca,']'
                            answer=raw_input('return to keep default  ')
                            try:
                                end_pca=int(answer) 
                                if plotblock[beg_pca][5]=='b' or plotblock[end_pca][5]=='b': 
                                    print "Can't select 'bad' measurement for PCA bounds -try again"
                                    end_pca=len(plotblock)-1
                                    beg_pca=0
                                elif beg_pca >=0 and beg_pca<=len(plotblock)-2 and end_pca>0 and end_pca<len(plotblock): 
                                    GoOn=1
                                else:
                                    print beg_pca,end_pca, " are bad entry of indices - try again"
                                    end_pca=len(plotblock)-1
                                    beg_pca=0
                            except:
                                print beg_pca,end_pca, " are bad entry of indices - try again"
                                end_pca=len(plotblock)-1
                                beg_pca=0
                        GoOn=0
                        while GoOn==0:
                            if calculation_type!="":
                                print "Prior calculation type = ",calculation_type
                            ct=raw_input('Enter new Calculation Type: best-fit line,  plane or fisher mean [l]/p/f :  ' )
                            if ct=="" or ct=="l": 
                                direction_type="l"
                                calculation_type="DE-BFL"
                                GoOn=1
                            elif ct=='p':
                                direction_type="p"
                                calculation_type="DE-BFP"
                                GoOn=1
                            elif ct=='f':
                                direction_type="l"
                                calculation_type="DE-FM"
                                GoOn=1
                            else: 
                                print "bad entry of calculation type: try again. "
                        pmagplotlib.plotZED(ZED,plotblock,angle,s,units)
                        if verbose:pmagplotlib.drawFIGS(ZED)
                        if geo==1 and tilt==0:
                            mpars=pmag.domean(geoblock,beg_pca,end_pca,calculation_type)
                            if mpars['specimen_direction_type']=='Error':break
                            PmagSpecRec["specimen_dec"]='%7.1f ' %(mpars["specimen_dec"])
                            PmagSpecRec["specimen_inc"]='%7.1f ' %(mpars["specimen_inc"])
                            if "SO-NO" not in method_codes:
                                PmagSpecRec["specimen_tilt_correction"]='0'
                                method_codes.append("DA-DIR-GEO")
                            else:
                                PmagSpecRec["specimen_tilt_correction"]='-1'
                            pmagplotlib.plotDir(ZED,mpars,geoblock,angle)
                            if verbose:pmagplotlib.drawFIGS(ZED)
                        if geo==1 and  tilt==1:
                            mpars=pmag.domean(tiltblock,beg_pca,end_pca,calculation_type)
                            if mpars['specimen_direction_type']=='Error':break
                            PmagSpecRec["specimen_dec"]='%7.1f ' %(mpars["specimen_dec"])
                            PmagSpecRec["specimen_inc"]='%7.1f ' %(mpars["specimen_inc"])
                            if "SO-NO" not in method_codes:
                                PmagSpecRec["specimen_tilt_correction"]='100'
                                method_codes.append("DA-DIR-TILT")
                            else:
                                PmagSpecRec["specimen_tilt_correction"]='-1'
                            pmagplotlib.plotDir(ZED,mpars,tiltblock,angle)
                            if verbose:pmagplotlib.drawFIGS(ZED)
                        if geo==0 and tilt==0: 
                            mpars=pmag.domean(datablock,beg_pca,end_pca,calculation_type)
                            if mpars['specimen_direction_type']=='Error':break
                            PmagSpecRec["specimen_dec"]='%7.1f ' %(mpars["specimen_dec"])
                            PmagSpecRec["specimen_inc"]='%7.1f ' %(mpars["specimen_inc"])
                            PmagSpecRec["specimen_tilt_correction"]='-1'
                            pmagplotlib.plotDir(ZED,mpars,plotblock,angle)
                            if verbose:pmagplotlib.drawFIGS(ZED)
                        PmagSpecRec["measurement_step_min"]='%8.3e ' %(mpars["measurement_step_min"])
                        PmagSpecRec["measurement_step_max"]='%8.3e ' %(mpars["measurement_step_max"])
                        PmagSpecRec["specimen_correction"]='u'
                        PmagSpecRec["specimen_dang"]='%7.1f ' %(mpars['specimen_dang'])
                        print 'DANG: ',PmagSpecRec["specimen_dang"]
                        if calculation_type!='DE-FM':
                            PmagSpecRec["specimen_mad"]='%7.1f ' %(mpars["specimen_mad"])
                            PmagSpecRec["specimen_alpha95"]=""
                        else:
                            PmagSpecRec["specimen_alpha95"]='%7.1f ' %(mpars["specimen_alpha95"])
                            PmagSpecRec["specimen_mad"]=""
                        PmagSpecRec["specimen_n"]='%i ' %(mpars["specimen_n"])
                        PmagSpecRec["specimen_direction_type"]=direction_type
                        PmagSpecRec["calculation_type"]=calculation_type # redundant and won't be imported - just for convenience
                        method_codes=PmagSpecRec["magic_method_codes"].split(':')
                        if len(method_codes) != 0:
                            methstring=""
                            for meth in method_codes:
                                ctype=meth.split('-')
                                if 'DE' not in ctype:methstring=methstring+ ":" +meth # don't include old direction estimation methods
                        methstring=methstring+':'+calculation_type
                        PmagSpecRec["magic_method_codes"]= methstring.strip(':')
                        print 'Method codes: ',PmagSpecRec['magic_method_codes']
                        if calculation_type!='DE-FM':
                            if units=='K': 
                                print '%s %i %7.1f %7.1f %7.1f %7.1f %7.1f %7.1f, %s \n' % (PmagSpecRec["er_specimen_name"],int(PmagSpecRec["specimen_n"]),float(PmagSpecRec["specimen_mad"]),float(PmagSpecRec["specimen_dang"]),float(PmagSpecRec["measurement_step_min"])-273,float(PmagSpecRec["measurement_step_max"])-273,float(PmagSpecRec["specimen_dec"]),float(PmagSpecRec["specimen_inc"]),calculation_type)
                            elif units== 'T':
                                print '%s %i %7.1f %7.1f %7.1f %7.1f %7.1f %7.1f, %s \n' % (PmagSpecRec["er_specimen_name"],int(PmagSpecRec["specimen_n"]),float(PmagSpecRec["specimen_mad"]),float(PmagSpecRec["specimen_dang"]),float(PmagSpecRec["measurement_step_min"])*1e3,float(PmagSpecRec["measurement_step_max"])*1e3,float(PmagSpecRec["specimen_dec"]),float(PmagSpecRec["specimen_inc"]),calculation_type)
                            elif 'T' in units and 'K' in units:
                                if float(PmagSpecRec['measurement_step_min'])<1.0 :
                                    min=float(PmagSpecRec['measurement_step_min'])*1e3
                                else:
                                    min=float(PmagSpecRec['measurement_step_min'])-273
                                if float(PmagSpecRec['measurement_step_max'])<1.0 :
                                    max=float(PmagSpecRec['measurement_step_max'])*1e3
                                else:
                                    max=float(PmagSpecRec['measurement_step_max'])-273
                                print '%s %i %7.1f %i %i %7.1f %7.1f %7.1f, %s \n' % (PmagSpecRec["er_specimen_name"],int(PmagSpecRec["specimen_n"]),float(PmagSpecRec["specimen_mad"]),float(PmagSpecRec["specimen_dang"]),min,max,float(PmagSpecRec["specimen_dec"]),float(PmagSpecRec["specimen_inc"]),calculation_type)
                            else:
                                print '%s %i %7.1f %7.1f %7.1f %7.1f %7.1f %7.1f, %s \n' % (PmagSpecRec["er_specimen_name"],int(PmagSpecRec["specimen_n"]),float(PmagSpecRec["specimen_mad"]),float(PmagSpecRec["specimen_dang"]),float(PmagSpecRec["measurement_step_min"]),float(PmagSpecRec["measurement_step_max"]),float(PmagSpecRec["specimen_dec"]),float(PmagSpecRec["specimen_inc"]),calculation_type)
                        else:
                            if 'K' in units:
                                print '%s %i %7.1f %7.1f %7.1f %7.1f %7.1f %7.1f, %s \n' % (PmagSpecRec["er_specimen_name"],int(PmagSpecRec["specimen_n"]),float(PmagSpecRec["specimen_alpha95"]),float(PmagSpecRec["specimen_dang"]),float(PmagSpecRec["measurement_step_min"])-273,float(PmagSpecRec["measurement_step_max"])-273,float(PmagSpecRec["specimen_dec"]),float(PmagSpecRec["specimen_inc"]),calculation_type)
                            elif 'T' in units:
                                print '%s %i %7.1f %7.1f %7.1f %7.1f %7.1f %7.1f, %s \n' % (PmagSpecRec["er_specimen_name"],int(PmagSpecRec["specimen_n"]),float(PmagSpecRec["specimen_alpha95"]),float(PmagSpecRec["specimen_dang"]),float(PmagSpecRec["measurement_step_min"])*1e3,float(PmagSpecRec["measurement_step_max"])*1e3,float(PmagSpecRec["specimen_dec"]),float(PmagSpecRec["specimen_inc"]),calculation_type)
                            elif 'T' in units and 'K' in units:
                                if float(PmagSpecRec['measurement_step_min'])<1.0 :
                                    min=float(PmagSpecRec['measurement_step_min'])*1e3
                                else:
                                    min=float(PmagSpecRec['measurement_step_min'])-273
                                if float(PmagSpecRec['measurement_step_max'])<1.0 :
                                    max=float(PmagSpecRec['measurement_step_max'])*1e3
                                else:
                                    max=float(PmagSpecRec['measurement_step_max'])-273
                                print '%s %i %7.1f %i %i %7.1f %7.1f, %s \n' % (PmagSpecRec["er_specimen_name"],int(PmagSpecRec["specimen_n"]),float(PmagSpecRec["specimen_alpha95"]),min,max,float(PmagSpecRec["specimen_dec"]),float(PmagSpecRec["specimen_inc"]),calculation_type)
                            else:
                                print '%s %i %7.1f %7.1f %7.1f %7.1f %7.1f, %s \n' % (PmagSpecRec["er_specimen_name"],int(PmagSpecRec["specimen_n"]),float(PmagSpecRec["specimen_alpha95"]),float(PmagSpecRec["measurement_step_min"]),float(PmagSpecRec["measurement_step_max"]),float(PmagSpecRec["specimen_dec"]),float(PmagSpecRec["specimen_inc"]),calculation_type)
                        saveit=raw_input("Save this interpretation? [y]/n \n")
                        if saveit!="n":
                            changeS=1
#
# put in details
#
                            angle,direction_type,setangle="","",0
                            if len(CurrRecs)>0:
                                replace=raw_input(" [0] add new component, or [1] replace existing interpretation(s) [default is replace] ")
                                if replace=="1" or replace=="":
                                    CurrRecs=[]
                                    PmagSpecRec['specimen_comp_name']='A'
                                    CurrRecs.append(PmagSpecRec)
                                else:
                                    print 'These are the current component names for this specimen: '
                                    for trec in CurrRecs:print trec['specimen_comp_name']
                                    compnum=raw_input("Enter new component name: ")
                                    PmagSpecRec['specimen_comp_name']=compnum
                                    print "Adding new component: ",PmagSpecRec['specimen_comp_name']
                                    CurrRecs.append(PmagSpecRec)
                            else:
                                PmagSpecRec['specimen_comp_name']='A'
                                CurrRecs.append(PmagSpecRec)
                            k+=1 
                            ans=""
                        else:
                            ans=""
              else:  # plots=1
                  k+=1
                  files={}
                  locname.replace('/','-')
                  print PmagSpecRec
                  for key in ZED.keys():
                      files[key]="LO:_"+locname+'_SI:_'+PmagSpecRec['er_site_name']+'_SA:_'+PmagSpecRec['er_sample_name']+'_SP:_'+s+'_CO:_'+coord+'_TY:_'+key+'_.'+fmt
                  if pmagplotlib.isServer:
                      black     = '#000000'
                      purple    = '#800080'
                      titles={}
                      titles['demag']='DeMag Plot'
                      titles['zijd']='Zijderveld Plot'
                      titles['eqarea']='Equal Area Plot'
                      ZED = pmagplotlib.addBorders(ZED,titles,black,purple)
                  pmagplotlib.saveP(ZED,files)
            if len(CurrRecs)>0:
                for rec in CurrRecs: PriorRecs.append(rec)
            if changeS==1:
                if len(PriorRecs)>0:
                    save_redo(PriorRecs,inspec)
                else:
                    os.system('rm '+inspec)
            CurrRecs,beg_pca,end_pca=[],"","" # next up
            changeS=0
        else: k+=1 # skip record - not enough data
    if changeM==1:
        pmag.magic_write(meas_file,meas_data,'magic_measurements')

if __name__ == "__main__":
    main()

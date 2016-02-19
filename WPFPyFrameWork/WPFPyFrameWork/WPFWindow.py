# define base class framework for Python.Net interface with WPF

import clr, System
clr.AddReference(r"wpf\PresentationFramework")
from System import IO, Windows, Threading
from System import TimeSpan

class WPFWindow(object):
    """
    Wrapper class for Systems.Window.Window class. Create and save WPF/XAML window in Window attribute
    All member functions and attributes can be directly accessed regardless of thread. The wrapper class
    automatically use the proper mechanism to handle messaging neccessary between different threads
    """
    
    def __init__(self, xamlFile=None, show=True , ownThread = False, modal = False):
        """ xamlFile:   xamlFile to create Window object
            show:       show the window during construction
            ownThread:  create a separate thread for this window
            modal:      block input of other windows (in the same thread)
        """
        self.XamlFile=xamlFile
        self.ownThread = ownThread
        self.modal = modal
        self.InitWindow(show)

    def __getattr__(self, item):
        """ for attributes that are missing (by __getattribute__) construct from Window object """
        # To-Do: need to make thread aware 
        tmp = self.Window.FindName(item)
        if tmp == None:
            raise AttributeError("%s does not have % attribute/control" %(self.Window.Title, item))
        else:
            return self.Wndow.FindName(item)



class WPFPyWindow(Windows.Window):
# the base class for all WPF windows
# assumed to be launched from an UIthread, and work within UIThread's dispatch and context
# does not handle threading etc

    def __getattr__(self, item):
    # map value to attribute, only call if there is no attribute with this name
        return self.FindName(item)

    def InitWindow(self, show=True, modal=False):
    ## initialize window
        try:
            stream = IO.StreamReader(self.XamlFile)
            newWindow =  Windows.Markup.XamlReader.Load(stream.BaseStream)
        except Exception as e:
            print e
            raise
    
        if show: 
            if modal:
                self.ShowDialog()
            else:
                self.Show()
        self.InitControls()
        self.InitCustomizeControls()

    def InitControls(self):
    # default control initiation for all windows
        pass

    def InitCustomizeControls(self):
    # interface allow child class to further customize controls
        pass

    def GetControl(self,name):
        tmp = self.FindName(name)
        if tmp == None:
            raise AttributeError("%s window does not have %s control" % (self.Title, name))
        else:
            return tmp
 
class WPFPyBase(object):
# the base class for all WPF window
# load xaml and create window object

    def __init__(self, xamlFile, block=True):
    # block: whether to block calling thread
        self.XamlFile = xamlFile
        self.Block = block
        self.evt = Threading.AutoResetEvent(False)
        self.Application = None
        self.CreateThread(block)


    def CreateThread(self, block=True):
    # block: whether block return to current thread
        thread = Threading.Thread(Threading.ThreadStart(self.ThreadStart))
        thread.IsBackground = True
        self.Thread = thread
        thread.SetApartmentState(Threading.ApartmentState.STA)
        thread.Start()
        # wait for window creation before continue
        self.evt.WaitOne() 
        # block calling thread or not
        if block:
           thread.Join()
        return self.Thread


    # two functions below will execute function in UIThread, use associated context
    # created during initial window construction. 
    # execute "func" with "arg" parameter: arg parameter is single object (can be a list)
    # to pass parameter and get return, use the default class namespace "self." 
    def PostToUIThread(self,func, arg=None):
    # Post: execute sync, also pass back exception, handled by calling thread
        self.Context.Post( Threading.SendOrPostCallback(func), arg )

    def SendToUIThread(self,func, arg=None):
    # Send:  execute async, will not pass back exceptop, handled by UIThread
        self.Context.Send( Threading.SendOrPostCallback(func), arg )


#  =====
#  Below methods are executed in its own separate thread of created window
#  =====
    def ThreadStart(self):
        self.InitWindow()
        if Windows.Application.Current == None:
            self.Application = Windows.Application()
            self.Application.Run()
        else:
            Windows.Threading.Dispatcher.Run()

    def ThreadShutdown(self,s,e):
        # shuts down the Dispatcher when the window closes
        Windows.Threading.Dispatcher.CurrentDispatcher.BeginInvokeShutdown(Windows.Threading.DispatcherPriority.Background)

    def InitWindow(self):
    # initialization explicitly called from STA environment to read xaml and initialize window
        
        #  forces the synchronization context to be in place before the Window gets created
        #  UI thread is different from the worker thread (calling thread) need context to mashel into UI thread
        self.Context = Threading.SynchronizationContext.Current
        if self.Context == None:
            self.Context =  Windows.Threading.DispatcherSynchronizationContext(Windows.Threading.Dispatcher.CurrentDispatcher)
            Threading.SynchronizationContext.SetSynchronizationContext(self.Context)  
     
        self.Stream = IO.StreamReader(self.XamlFile)
        self.MainWindow = Windows.Markup.XamlReader.Load(self.Stream.BaseStream)
        self.MainWindow.Closed += self.ThreadShutdown
        self.MainWindow.Show()
        # notify window creation completed
        self.evt.Set()
        self.InitControls()
        self.InitCustomizeControls()


      


import logging
import logging.handlers
import queue
import atexit
from core.middleware import get_current_request_id, get_current_user_id

class ContextFilter(logging.Filter):
    """
    Injects request_id and user_id from the current thread-local context
    into the log record if they exist.
    """
    def filter(self, record):
        record.request_id = get_current_request_id()
        record.user_id = get_current_user_id()
        return True


def setup_async_logging():
    """
    Finds the specific file handlers configured by Django, removes them from the root
    and specific loggers, and wraps them in a QueueHandler. 
    A QueueListener is then started in a background thread to process logs asynchronously,
    preventing any file I/O operations from blocking the web request cycle.
    """
    loggers = [logging.getLogger(), logging.getLogger('django')]
    
    # We will aggregate all file handlers we find across loggers
    file_handlers = []
    
    for logger in loggers:
        handlers_to_remove = []
        for handler in logger.handlers:
            if isinstance(handler, logging.handlers.TimedRotatingFileHandler) or isinstance(handler, logging.FileHandler):
                file_handlers.append(handler)
                handlers_to_remove.append(handler)
                
        # Remove them so they don't block
        for handler in handlers_to_remove:
            logger.removeHandler(handler)
            
    # Deduplicate handlers
    unique_file_handlers = list(set(file_handlers))
    
    if not unique_file_handlers:
        return

    # Create the async queue
    log_queue = queue.Queue(-1)
    
    # Create the queue handler that drops logs into the queue
    queue_handler = logging.handlers.QueueHandler(log_queue)
    
    # Add the queue handler back to the loggers
    for logger in loggers:
        logger.addHandler(queue_handler)
        
    # Start the listener in a background thread that pulls from the queue and writes to the files
    listener = logging.handlers.QueueListener(log_queue, *unique_file_handlers, respect_handler_level=True)
    listener.start()
    
    # Ensure graceful shutdown of the listener thread on exit
    atexit.register(listener.stop)

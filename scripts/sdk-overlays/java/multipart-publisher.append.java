  /** Owns the generated Apache multipart serializer's producer and both pipe ends. */
  private static final class MultipartBodyPublisher implements HttpRequest.BodyPublisher, AutoCloseable {
    private final HttpEntity entity;
    private final java.util.Set<Upload> active = new java.util.HashSet<>();
    private final HttpRequest.BodyPublisher delegate = HttpRequest.BodyPublishers.ofInputStream(this::open);
    private boolean closed;

    MultipartBodyPublisher(HttpEntity entity) {
      this.entity = entity;
    }

    @Override public long contentLength() { return delegate.contentLength(); }

    @Override public void subscribe(java.util.concurrent.Flow.Subscriber<? super java.nio.ByteBuffer> subscriber) {
      delegate.subscribe(subscriber);
    }

    private synchronized InputStream open() {
      if (closed) throw new IllegalStateException("Multipart upload is closed.");
      try {
        Upload upload = new Upload(Pipe.open());
        active.add(upload);
        upload.producer.start();
        return upload;
      } catch (IOException error) {
        throw new java.io.UncheckedIOException(new IOException("Multipart upload could not start."));
      }
    }

    @Override public void close() {
      java.util.List<Upload> uploads;
      synchronized (this) {
        if (closed) return;
        closed = true;
        uploads = new java.util.ArrayList<>(active);
        active.clear();
      }
      for (Upload upload : uploads) upload.close();
    }

    private final class Upload extends InputStream {
      private final Pipe pipe;
      private final InputStream source;
      private final Thread producer;
      private volatile IOException failure;
      private boolean stopped;

      Upload(Pipe pipe) {
        this.pipe = pipe;
        source = Channels.newInputStream(pipe.source());
        producer = new Thread(() -> {
          try {
            entity.writeTo(Channels.newOutputStream(pipe.sink()));
          } catch (IOException | RuntimeException error) {
            // No document path, bytes, or raw exception may escape through stderr.
            // Record failure before closing the sink makes EOF visible to the reader.
            failure = new IOException("Multipart upload could not be produced.");
          } finally {
            closeChannel(pipe.sink());
          }
        }, "cogneris-sdk-upload");
        producer.setDaemon(true);
      }

      @Override public int read() throws IOException {
        int result = source.read();
        if (result < 0 && failure != null) throw failure;
        return result;
      }

      @Override public int read(byte[] bytes, int offset, int length) throws IOException {
        int result = source.read(bytes, offset, length);
        if (result < 0 && failure != null) throw failure;
        return result;
      }

      @Override public void close() {
        synchronized (this) {
          if (stopped) return;
          stopped = true;
        }
        // Close channels directly: a blocked Channels input stream can hold its read monitor.
        closeChannel(pipe.source());
        closeChannel(pipe.sink());
        producer.interrupt();
        boolean interrupted = Thread.interrupted();
        try {
          long start = System.nanoTime();
          while (producer.isAlive() && producer != Thread.currentThread()) {
            long left = 1_000_000_000L - (System.nanoTime() - start);
            if (left <= 0) break;
            try { producer.join(left / 1_000_000, (int) (left % 1_000_000)); }
            catch (InterruptedException error) { interrupted = true; }
          }
        } finally {
          if (interrupted) Thread.currentThread().interrupt();
          synchronized (MultipartBodyPublisher.this) { active.remove(this); }
        }
      }
    }

    private static void closeChannel(java.nio.channels.Channel channel) {
      try { channel.close(); } catch (IOException ignored) { }
    }
  }

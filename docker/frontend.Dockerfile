# syntax=docker/dockerfile:1
FROM nginx:alpine as production

# Provide a simple placeholder until the frontend app is implemented.
RUN printf '%s\n' \
  '<!doctype html>' \
  '<html lang="en">' \
  '<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Cover Regulatory Engine</title></head>' \
  '<body><main><h1>Cover Regulatory Engine</h1><p>Frontend scaffold is deployed. Application UI will be added in a later task.</p></main></body>' \
  '</html>' \
  > /usr/share/nginx/html/index.html

# Copy nginx configuration
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]

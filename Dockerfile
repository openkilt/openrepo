# Start with a node.js build image to compile the vue.js app distributables
FROM node:18.11.0 AS vuebuilder

WORKDIR /build/reposio/

COPY frontend/ ./

RUN npm install && \
    npm run build

# Web app is compiled now to /build/reposio/dist/


# Now build the production image
FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
      apt-utils          \
      createrepo-c       \
      curl               \
      git                \   
      gpg                \
      gzip               \
      libapt-pkg-dev     \
      python3            \
      python3-pip        \
      nginx
      
WORKDIR /app


# Copy the requirements.txt first and install dependencies, so that this can be cached
COPY web/requirements.txt ./django/requirements.txt
RUN ln -s /usr/bin/python3 /usr/bin/python && \
    pip3 install --no-cache-dir -r django/requirements.txt && \
    mkdir -p /var/lib/openrepo/packages/

# Copy compiled vue app
COPY --from=vuebuilder /build/reposio/dist ./frontend-dist/

# Copy Django app and configuration
COPY web ./django
COPY deploy/nginx/nginx.conf.prod /etc/nginx/nginx.conf
COPY deploy/run_openrepoweb /usr/bin/


#CMD ["/usr/bin/run_openrepoweb"]
#EXPOSE 8000

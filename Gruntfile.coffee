module.exports = (grunt) ->

  jsdeps = [
    'jquery/dist/jquery'
    'moment/moment'
    'fullcalendar/dist/fullcalendar'
    'fullcalendar/dist/lang/fr'
  ].map (js) -> "#{['bower_components', js].join '/'}.js"

  cssdeps = [
    'fullcalendar/dist/fullcalendar'
  ].map (css) -> "#{['bower_components', css].join '/'}.css"

  grunt.initConfig
    pkg: grunt.file.readJSON('package.json')

    fileExists:
      js: jsdeps
      css: cssdeps

    uglify:
      options:
        banner: '/*! <%= pkg.name %>
           <%= grunt.template.today("yyyy-mm-dd") %> */\n'
        sourceMap: true

      holiday:
        files:
          'static/main.min.js': 'static/main.js'

      deps:
        files:
          'static/deps.min.js': jsdeps

    cssmin:
      options:
        noAdvanced: true
      deps:
        files:
          'static/deps.min.css': cssdeps

    sass:
      holiday:
        expand: true
        cwd: 'sass'
        src: '*.sass'
        dest: 'static/'
        ext: '.css'

    autoprefixer:
      hydra:
        expand: true
        cwd: 'static/'
        src: '*.css'
        dest: 'static/'

    coffee:
      holiday:
        files:
          'static/main.js': 'coffee/*.coffee'

    coffeelint:
      holiday:
        'coffee/*.coffee'

    watch:
      all:
        files: [
          'coffee/*.coffee'
          'Gruntfile.coffee'
          'sass/*.sass'
        ]
        tasks: ['default']

  grunt.loadNpmTasks 'grunt-contrib-coffee'
  grunt.loadNpmTasks 'grunt-contrib-watch'
  grunt.loadNpmTasks 'grunt-contrib-uglify'
  grunt.loadNpmTasks 'grunt-file-exists'
  grunt.loadNpmTasks 'grunt-contrib-cssmin'
  grunt.loadNpmTasks 'grunt-autoprefixer'
  grunt.loadNpmTasks 'grunt-coffeelint'
  grunt.loadNpmTasks 'grunt-sass'
  grunt.registerTask 'default', [
    'fileExists', 'coffeelint', 'coffee', 'sass',
     'autoprefixer', 'cssmin', 'uglify']

"use strict";

var esaApp = angular.module("esaApp", [
    "ngRoute"
]);

esaApp.config(["$routeProvider",
     function($routeProvider) {
         $routeProvider.
             when("/", {
                 templateUrl: "/static/html/partials/search.html"
             }).
             when("/about", {
                 templateUrl: "../static/html/partials/about.html"
             }).
             otherwise({
                 redirectTo: "/"  // TODO: 404 page
             });
     }
]);

esaApp.controller("searchController", function ($scope, $http) {
    $scope.search = { };

    $scope.submit = function () {
        console.log("Search submitted");
        var terms = $scope.search.query;
        $http.get("/search?q=" + terms)
            .success(function (response) {
                $scope.search.hits = response.hits;
                $scope.search.queryTime = response.query_time_ms;
                $scope.search.queryConcepts = response.query_concepts;
                console.log("Search successful");
            })
            .error(function (error, status) { // TODO: "search temporarily unavailable" on 5xx
                $scope.search.error = { message: error.message, status: status };
                console.log(error.message)
        });
    };

});

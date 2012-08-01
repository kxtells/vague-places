/***********************************************************************

Takes a list of points and returns a CSV with the correspondent linestrings.


[-p] -> Returns the points of the edge

************************************************************************/

#include <CGAL/Exact_predicates_inexact_constructions_kernel.h>
#include <CGAL/Exact_predicates_exact_constructions_kernel.h>
#include <CGAL/algorithm.h>
#include <CGAL/Delaunay_triangulation_2.h>
#include <CGAL/Alpha_shape_2.h>
#include <CGAL/Boolean_set_operations_2.h>

#include <iostream>
#include <fstream>
#include <vector>
#include <list>


typedef CGAL::Exact_predicates_exact_constructions_kernel K;

typedef K::FT FT;

typedef K::Point_2  Point;
typedef K::Segment_2  Segment;
typedef CGAL::Polygon_2<K> Polygon_2;

typedef CGAL::Alpha_shape_vertex_base_2<K> Vb;
typedef CGAL::Alpha_shape_face_base_2<K>  Fb;
typedef CGAL::Triangulation_data_structure_2<Vb,Fb> Tds;
typedef CGAL::Delaunay_triangulation_2<K,Tds> Triangulation_2;

typedef CGAL::Alpha_shape_2<Triangulation_2>  Alpha_shape_2;

typedef Alpha_shape_2::Face  Face;
typedef Alpha_shape_2::Vertex Vertex;
typedef Alpha_shape_2::Edge Edge;
typedef Alpha_shape_2::Face_handle  Face_handle;
typedef Alpha_shape_2::Vertex_handle Vertex_handle;

typedef Alpha_shape_2::Face_circulator  Face_circulator;
typedef Alpha_shape_2::Vertex_circulator  Vertex_circulator;

typedef Alpha_shape_2::Locate_type Locate_type;

typedef Alpha_shape_2::Face_iterator  Face_iterator;
typedef Alpha_shape_2::Vertex_iterator  Vertex_iterator;
typedef Alpha_shape_2::Edge_iterator  Edge_iterator;
typedef Alpha_shape_2::Edge_circulator  Edge_circulator;

typedef Alpha_shape_2::Alpha_iterator Alpha_iterator;
typedef Alpha_shape_2::Alpha_shape_edges_iterator Alpha_shape_edges_iterator;
typedef Alpha_shape_2::Alpha_shape_vertices_iterator Alpha_shape_vertices_iterator;

//---------------------------------------------------------------------

template <class OutputIterator>
void
alpha_edges( const Alpha_shape_2&  A,
	     OutputIterator out)
{

  for(Alpha_shape_edges_iterator it =  A.alpha_shape_edges_begin();
      it != A.alpha_shape_edges_end();
      ++it){
      *out++ = A.segment(*it);
  }
}

template <class OutputIterator>
void
alpha_vertices( const Alpha_shape_2&  A,
	     OutputIterator out)
{

  for(Alpha_shape_vertices_iterator it =  A.alpha_shape_vertices_begin();
      it != A.alpha_shape_vertices_end();
      ++it){
      *out++ = Vertex_handle(*it);
  }
}

template <class OutputIterator>
bool
file_input(OutputIterator out)
{
  std::ifstream is("./data/fin", std::ios::in);

  if(is.fail()){
    std::cerr << "unable to open file for input" << std::endl;
    return false;
  }

  int n;
  is >> n;
  CGAL::copy_n(std::istream_iterator<Point>(is), n, out);

  return true;
}

//------------------ functions --------------------------------------


bool check_inside(Point pt, Polygon_2 pgn, K traits)
{
  //std::cout << "The point " << pt;
  switch(CGAL::bounded_side_2(pgn.vertices_begin(), pgn.vertices_end(), pt, traits)) {
    case CGAL::ON_BOUNDED_SIDE :
      //std::cout << " is inside the polygon.\n";
      return true;
    case CGAL::ON_BOUNDARY:
      //std::cout << " is on the polygon boundary.\n";
      return false;
    case CGAL::ON_UNBOUNDED_SIDE:
      //std::cout << " is outside the polygon.\n";
      return false;
  }
}

/**
* Checks if plg2 is inside plg1
*/
bool check_hole(Polygon_2 plg1, Polygon_2 plg2){
  bool ishole = true;
  for (std::vector<Point>::iterator v2 = plg2.vertices_begin();
      v2 != plg2.vertices_end();
      ++v2){
      if(! check_inside(*v2, plg1, K())){
        ishole = false;
        break; //stop checking
      }
  }
  return ishole;
}

/**
Prints a polygon in its WKT form
(p1,p2,p3,....)

Does not add POLYGON text. It is used inside other printing functions
*/
void print_WKT_polygon_2(Polygon_2 plg){
  
  std::cout << "(";
  for (std::vector<Point>::iterator v = plg.vertices_begin();
      v != plg.vertices_end();
      ++v){
      std::cout << *v << ",";
  }
  std::cout << ")";

}

/**
  This function tries to obtain an ordered list of the segments to form a polygon.
*/
void toWKT_polygon(std::vector<Segment> segments, const Alpha_shape_2& A){

  Segment cs;
  bool found = false;
  int pid = 0; //polygon id (possible alpha shape with different polygons)
  int count = 0;
  std::vector<Segment> osegments [255]; //initialize at 255. not more
  std::vector<Segment> segments_tmp;

  for(int i = 0; i < segments.size();i++){
    segments_tmp.push_back(segments[i]);
  }

  //push a first segment
  osegments[pid].push_back(segments_tmp.back());
  segments_tmp.pop_back(); //remove the element
  
  while(segments_tmp.size() > 0){
    cs = osegments[pid].back();
    found = false;

    for(std::vector<Segment>::iterator it = segments_tmp.begin(); 
        !found && it != segments_tmp.end();
        ++it){
        
        if (cs.target() == it->source()){
          found = true;
          osegments[pid].push_back(*it);
          segments_tmp.erase(it);
        }
    }

    if (!found){
      /*if not found. I assume that there is another polygon.
        Increase polygon id (pid) and keep going.
      */
      ++pid;
      osegments[pid].push_back(segments_tmp.back());
      segments_tmp.pop_back();
    }
  }
  

  //Prints all the polygons. Do not check if those are holes or not
  for(int i=0;i<255;i++){
    if(osegments[i].size()==0) break;
    
    std::cout << "POLYGON((";
    std::vector<Segment>::iterator it = osegments[i].begin();
    std::cout << it->source() << ","; //first point
    
    for(std::vector<Segment>::iterator it = osegments[i].begin(); it != osegments[i].end();++it,++count){
      std::cout << it->target() << ",";
    }
    std::cout << "))" << std::endl;
  }

  std::cout << "------" << std::endl;

  //TRYING MORE THINGS (determining the holes)
  //Create Polygon2 structures
  std::vector<Polygon_2> polygons; //initialize at 255. not more
  
  for(int i=0;i<255;i++){
    if(osegments[i].size()==0) break;
    Polygon_2 P;
    std::vector<Segment>::iterator it = osegments[i].begin();
    P.push_back(it->source()); //first point
    
    for(std::vector<Segment>::iterator it = osegments[i].begin(); it != osegments[i].end();++it){
      P.push_back(it->target());
    }
    polygons.push_back(P);
  }
  

  //Try to determine the holes and print it
  for(std::vector<Polygon_2>::iterator plg1 = polygons.begin(); plg1 != polygons.end();++plg1){
     //print the first polygon part
     std::cout << "POLYGON(";
     print_WKT_polygon_2(*plg1);

    //polygons.erase(plg1); //already printed, no need to check for him

    //check for holes, and print them with the polygon
    for(std::vector<Polygon_2>::iterator plg2 = polygons.begin(); plg2 != polygons.end();++plg2){

      if (check_hole(*plg1,*plg2)){ //finished, is a hole of the plg1
        std::cout << ",";
        print_WKT_polygon_2(*plg2);
      }
    }
    
    std::cout << ")" << std::endl;
  }

}

/**
* Prints a csv list of the Alpha shape segments
*/
void toWKT_segments(std::vector<Segment> segments, const Alpha_shape_2& A){

  std::cout << "id;wkt" << std::endl;
  int count = 0;

  for(std::vector<Segment>::iterator it = segments.begin(); it != segments.end();++it){
    std::cout << count << ";" << "LINESTRING(" << it->source() << "," << it->target() << ") " << std::endl;
    count++;
  }
  
}

void toWKT_vertices(std::vector<Vertex_handle> segments, const Alpha_shape_2& A){
  int count = 0; 
  
  std::cout << "id;wkt" << std::endl;
  for(std::vector<Vertex_handle>::iterator it = segments.begin(); it != segments.end();++it){
    Point p=(*it)->point();
    std::cout << count << ";" << "POINT(" << p[0] << " " << p[1] << ")" << std::endl;
    count++;
  }

  
}
//------------------ main -------------------------------------------

int main(int argc, char* argv[])
{
  //check points flag
  bool bpoints = false;
  float alpha = -1;
  for(int i =0; i < argc; i++){
    if (strcmp(argv[i],"-p")==0) {
        bpoints = true;
    }
    if (strcmp(argv[i],"-a") == 0){
        alpha = atof(argv[i+1]);
    }
  }


  //File Input
  std::list<Point> points;

  if(! file_input(std::back_inserter(points))){
    return -1;
  }

  //Alpha shape compute
  Alpha_shape_2 A(points.begin(), points.end());
  A.set_mode(Alpha_shape_2::GENERAL);
  
  if (alpha != -1){
    A.set_alpha(alpha);
  }
  else{
    Alpha_iterator opt = A.find_optimal_alpha(1);
    A.set_alpha(*opt);
  }
  
  
  std::vector<Segment> segments;
  std::vector<Vertex_handle> vertices;

  alpha_edges( A, std::back_inserter(segments));
  alpha_vertices( A, std::back_inserter(vertices));

  //print result
  if (bpoints){
    toWKT_vertices(vertices,A);
  }
  else{
    toWKT_segments(segments,A);
  }
 
  //@TEST polygon WKT
  toWKT_polygon(segments,A);
  std::cout << "END" << std::endl;
  return 0;
}

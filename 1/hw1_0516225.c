#include<stdio.h>
#include<string.h>
#include<pthread.h>
#include<stdlib.h>
#include<unistd.h>
typedef struct play{
	int id;
	int arrive_time;
	int rest_till;
	int round_per;
	int current_round;
	int rest;
	int round_total;
	int get_item;
	int order;
} data;
//<customer1 arrive time><continuously play round><rest time><total play round number N> 
pthread_t *tid;
data *play;
int machine1_avalible = 0;
int timer = -1;
int NUM_THREADS = 0;
int NUM_THREADS_for_detect = 0;
int g_num = 0;
int g_num_float = 0;
int in_use = 0;
int count_use = 0;
int task = 0;
pthread_cond_t cond = PTHREAD_COND_INITIALIZER;
pthread_mutex_t lock = PTHREAD_MUTEX_INITIALIZER;;

void* trythis(void *arg)
{	
	int pos = (int) arg;
	//printf("hi\n");
	//printf("timer = %d arrive_time = %d\n",timer, play[pos].arrive_time);
	while(play[pos].get_item != 1 ){ 							//?„æ?å¤¾åˆ°ä¹‹å? ?½çµ¦?‘å¤¾
		//printf("machine1_avalible %d\n", machine1_avalible);
		pthread_mutex_lock(&lock);
		int current_time = timer ;
		//printf("round_total = %d ",play[pos].round_total);
		if(play[pos].arrive_time == timer){
			if(machine1_avalible == timer && in_use != 0){
				//printf("machine1_avalible %d\n", timer);
				pthread_cond_wait(&cond, &lock);
				//goto END;
			}
			if(in_use == 0){
				if(search_frist() != pos){
					goto END;
				}
				if(g_num_float == g_num) {
					printf("%d %d finish playing YES\n", timer, play[pos].id);
						play[pos].get_item = 1;
						g_num_float = 0;
						play[pos].order = 100000;
						in_use = 0;
						goto END;
				}
				play[pos].current_round = min(play[pos].round_per,play[pos].round_total);
				printf("%d %d start playing\n", timer, play[pos].id);
				machine1_avalible = max(machine1_avalible,timer + play[pos].current_round);
				//printf("timr %d + current_round %d\n",timer, play[pos].current_round);
				play[pos].current_round --;
				play[pos].round_total -- ;
				in_use = play[pos].id;
				g_num_float ++;

			}
			else if(in_use != play[pos].id){
				printf("%d %d wait in line \n", timer, play[pos].id);
				//play[pos].order = timer ;
			}
		}
		else if(play[pos].arrive_time < timer){
			if(in_use == 0){
				if(search_frist() != pos){
					goto END;
				}
				//pthread_cond_signal(&cond);
				if(g_num_float == g_num) {
					printf("%d %d finish playing YES\n", timer, play[pos].id);
						play[pos].get_item = 1;
						g_num_float = 0;
						play[pos].order = 100000;
						in_use = 0;
						goto END;
				}
				play[pos].current_round = min(play[pos].round_per,play[pos].round_total);
				printf("%d %d start playing\n", timer, play[pos].id);
				machine1_avalible = max(machine1_avalible, timer + play[pos].current_round);
				//printf("timr %d + current_round %d\n",timer, play[pos].current_round);	
				play[pos].current_round --;
				play[pos].round_total --;
				g_num_float ++;
				in_use = play[pos].id;
			}
			else if(in_use == play[pos].id){			
				pthread_cond_signal(&cond);
				if(play[pos].current_round>0){
					if(g_num_float == g_num) {
						printf("%d %d finish playing YES\n", timer, play[pos].id);
							play[pos].get_item = 1;
							g_num_float = 0;
							play[pos].order = 100000;
							in_use = 0;
							goto END;
					}	
					play[pos].current_round --;
					play[pos].round_total -- ;
					g_num_float ++;
				}
				else if(play[pos].current_round == 0){
					in_use = 0;
					if(g_num_float == g_num) {
						printf("%d %d finish playing YES\n", timer, play[pos].id);
							play[pos].get_item = 1;
							g_num_float = 0;
							play[pos].order = 100000;
							in_use = 0;
							goto END;
					}	
					if(play[pos].round_total == 0){
						printf("%d %d finish playing YES\n", timer, play[pos].id);
						play[pos].get_item = 1;
						g_num_float = 0;
						play[pos].order = 100000;

					}
					else{
						printf("%d %d finish playing NO\n", timer, play[pos].id);
						//printf("rest_till = %d, rest = %d\n", play[pos].rest_till, play[pos].rest);
						play[pos].arrive_time = timer + play[pos].rest;
						play[pos].order = timer + play[pos].rest;
						

					}
				}				
			}
		}
		//while(current_time == timer){
			//printf("wait\n");
			//sleep(1);

		END : pthread_cond_wait(&cond, &lock);
		pthread_mutex_unlock(&lock);
		
	}
	NUM_THREADS_for_detect -- ;
	return NULL;
}
void* timer_control(void *arg){
	while(NUM_THREADS_for_detect > 0){
		//printf("%d %d g_num_float = %d\n",timer,in_use,g_num_float);
		//if()
		//sleep(1);
		pthread_mutex_lock(&lock);
		//printf("timer = %d and in_use = %d ",timer,in_use);
		if(in_use == 0){
			g_num_float = 0;
		}
		timer ++;
		//printf("counter = %d\n", count_use);
		//printf("Wake up all waiting threads...\n");
		pthread_mutex_unlock(&lock);
		pthread_cond_broadcast(&cond);
		//count_use = 0;
		usleep(2000);

	}
	return NULL;
}

int search_frist(){
	int tmp = play[0].order, location=0 ;
	//printf("in the array are: %d ", tmp);
	for(int i = 1 ; i< NUM_THREADS ; i++){
		//printf("%d ",play[i].order);
        if (play[i].order < tmp) 
        {
           tmp = play[i].order;
           location = i;
        }
	}
	//printf("\nmin arrive_time location = %d\n",location);
	return location;
}
int min(int num1, int num2)
{
    return (num1 < num2 ) ? num1 : num2;
}
int max(int num1, int num2)
{
    return (num1 > num2 ) ? num1 : num2;
}
int main(int argc,char **argv)
{
	FILE * fp;
	int i = 0;
	int error;
	//printf("%d",argc);
	fp = fopen(argv[1],"r");
	fscanf(fp,"%d %d",&g_num,&NUM_THREADS);
	NUM_THREADS_for_detect = NUM_THREADS;
	//g_num_float = g_num ;
	//printf("%d %d\n",g_num,NUM_THREADS);
	play = malloc(NUM_THREADS * sizeof(data));
	tid = malloc((NUM_THREADS+1) * sizeof(pthread_t));
	if (pthread_mutex_init(&lock, NULL) != 0)
	{
		printf("\n mutex init has failed\n");
		return 1;
	}
	for(i = 0 ; i < NUM_THREADS ; i++){
		fscanf(fp,"%d %d %d %d\n",&play[i].arrive_time,&play[i].round_per,&play[i].rest,&play[i].round_total);
		play[i].id = i+1;
		play[i].get_item = 0 ;
		play[i].current_round = 0;
		play[i].rest_till = 0;
		play[i].order = play[i].arrive_time;
	}

	error = pthread_create(&(tid[NUM_THREADS]), NULL, timer_control, NULL);
	if (error != 0){
		printf("\nThread can't be created :[%s]", strerror(error));
	}
	for(i = 0 ; i < NUM_THREADS ; i++)
	{	
		error = pthread_create(&(tid[i]), NULL, trythis, (void*) i);
		//NUM_THREADS_for_detect ++;
		if (error != 0){
			printf("\nThread can't be created :[%s]", strerror(error));
		}
	}

	for( i = 0 ; i <= NUM_THREADS ;i++){
		pthread_join(tid[i], NULL);	
	}

	pthread_mutex_destroy(&lock);

	return 0;
}

import { Injectable } from '@angular/core';
import { CanActivate, Router, ActivatedRouteSnapshot, RouterStateSnapshot } from '@angular/router';
import { Http } from '@angular/http';

import 'rxjs/add/operator/toPromise';

import { Repository } from '../repository/repository.model';
import { RepositoryService } from '../repository/repository.service';
import { UserIsAuthedGuard } from './user-auth.service';

@Injectable()
export class UserCantApproveRepoGuard implements CanActivate {
    constructor(
        private http: Http,
        private repositoryService: RepositoryService,
        private authGuard: UserIsAuthedGuard,
        private router: Router
    ) {}

    canActivate(route: ActivatedRouteSnapshot, state: RouterStateSnapshot) {
        let uuid = route.params['uuid'];

        // Only run this check if user successfully logged in.
        return this.authGuard.canActivate(route, state).then((auth: boolean) => {
            if(!auth) {
               return false;
            } else {
                return this.repositoryService
                    .fetchBasicInfo(uuid)
                    .then((repository) => {
                        // If repo is now active, send em' over.
                        if (repository.status == 'active') {
                            this.router.navigate(['/repos', repository.login, repository.name, 'set-up', 'email']);
                            return false;
                        // Otherwise, give em them bad news.
                        } else {
                            return true;
                        }
                    })
                    .catch((error: any) => {
                        // Usually a 404.
                        // User is authenticated, so we'll redirect them somewhere useful.
                        this.router.navigate(['/repos']);
                        return false;
                    });
            }
        });
    }
}
